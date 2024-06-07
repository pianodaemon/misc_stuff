#!/usr/bin/perl
use strict;
use warnings;

use File::stat;
use Storable qw(nstore retrieve);
use Digest::MurmurHash3 qw(murmur32);
use Mojo::Redis;

use constant { true => 1, false => 0, BF_CHECK => 0, BF_ADD => 1 };

our $debug = true;

sub _boolean_action_handler {
    my ($redis_conn, $redis_command, $res_expected, $key, $elem) = @_;

    my $rc = undef;
    my $promise = $redis_conn->db->call_p($redis_command, $key, "$elem");
    $promise->then(sub {
        my $res = shift;
        $debug and printf STDERR "_boolean_action_handler [%s] -> %s %s returning %s\n", $redis_command, $key, "$elem" ,$res;
        $rc = $res eq $res_expected ? true : false;
    })->catch(sub {
        my $err = shift;
        warn "Error: $err";
    })->wait;

    return $rc;
}

sub _reserve_bloom_filter {
    my ($redis_conn, $key, $error_rate, $capacity) = @_;

    my $rc = undef;
    my $promise = $redis_conn->db->call_p('BF.RESERVE' => $key, $error_rate, $capacity);
    $promise->then(sub {
        my $res = shift;
        $debug and printf STDERR "_reserve_bloom_filter [BF.RESERVE] -> %s %s %s returning %s\n", $key, $error_rate, $capacity, $res;
        $rc = $res eq "OK" ? true : false;
    })->catch(sub {
        my $err = shift;
        warn "Error: $err";
    })->wait;

    return $rc;
}

sub _lookup_shm {
    my ($redis_conn, $shm_mem_key, $shm_mem_size) = @_;
    my @actions = (
        sub {
            # 'BF.EXISTS' features an integer reply: where "1" means that the item was already added with a high probabily,
            # and "0" means that such item had not been added to the filter.
            return _boolean_action_handler($redis_conn, 'BF.EXISTS', 1, $shm_mem_key, shift);
        },
        sub {
            # 'BF.ADD' features an integer reply: where "1" means that the item has been added successfully,
            # and "0" means that such item was already added to the filter.
            return _boolean_action_handler($redis_conn, 'BF.ADD', 1, $shm_mem_key, shift);
        },
    );

    if ($redis_conn->db->exists($shm_mem_key)) {
        $debug and print STDERR "Recovering share memory segment with key $shm_mem_key\n";
        return \@actions;
    }

    printf STDERR "Non-available share memory segment featuring key: $shm_mem_key\n";

    if (eval { _reserve_bloom_filter($redis_conn, $shm_mem_key, "0.01", "$shm_mem_size"); 1 }) {
        $debug and print STDERR "Setting up share memory segment with key $shm_mem_key\n";
        return \@actions;
    } else {
        $debug and printf STDERR "%s\n", $@ || 'Unknown failure';
        die "Not possible to harness a share memory segment with key $shm_mem_key\n";
    }
}

sub _create_reg {
    my ($file_path, $fetch_handler) = @_;
    nstore($fetch_handler->(), $file_path);
}

sub retrieve_register {
    my ($file_path, $ttl_expected) = @_;
    my $file_stat = stat($file_path) or die "Failed to retrieve cache register $file_path: $!\n";

    if (time - $file_stat->mtime > $ttl_expected) {
        unlink $file_path;
        die "Cache register has expired.\n";
    }

    $debug and print STDERR "Asking for content via cache\n";
    return retrieve($file_path);
}

sub _obtain_from_icss {
    my ($shared_ref, $kcache, $fetch_handler) = @_;
    my $kfpath = $kcache . ".cache";
    my $do_registration = sub {
      _create_reg($kfpath, $fetch_handler);
      return;
    };

    my $found_flag = $shared_ref->[BF_CHECK]->($kcache);
    if ($found_flag == 1) {
        RETRIEVE_POINT:
        my $sref;
        unless (eval {
          $sref = retrieve_register $kfpath, 30;
        }) {
          $debug and printf STDERR "%s\n", $@ || 'Unknown failure';
          &$do_registration();
          goto RETRIEVE_POINT;
        }
        print $$sref;
    } else {
        &$do_registration();
        $shared_ref->[BF_ADD]->($kcache);
        goto RETRIEVE_POINT;
    }
}

sub ping {
    my ($redis_conn) = @_;

    $debug and do {
        my $pong = $redis_conn->db->ping;
        die "Failed to ping Redis server" unless $pong eq 'PONG';
        print STDERR "Successfully pinged Redis server: $pong\n";
    };
}

sub do_conn {
    my ($host, $port) = @_;

    # Resource Acquisition Is Initialization or RAII
    Mojo::IOLoop->start unless Mojo::IOLoop->is_running;
    my $redis_conn = Mojo::Redis->new("redis://$host:$port/0")->encoding("UTF-8");
    ping($redis_conn);
    return $redis_conn;
}

sub do_disconn {
    my ($redis_conn) = @_;

    # Resource Acquisition Is Initialization or RAII
    undef $redis_conn;  # This will clean up the connection object
    Mojo::IOLoop->stop; # This will stop the event loop
}

sub do_cache {
    my ($redis_conn, $network_cache_key, $cache_size, $src_url, $fetch_handler) = @_;
    my $shared_ref = _lookup_shm($redis_conn, $network_cache_key, $cache_size);
    _obtain_from_icss($shared_ref, murmur32($src_url), $fetch_handler);
}


# From this point onward it is mostly explanatory regarding its correct usage.
{
    use LWP::UserAgent;
    sub fetcher_http_get_method {
        my $remote_url = shift;
        my $ua = LWP::UserAgent->new;

        print STDERR "Asking for remote content via HTTP GET\n";
        my $get_response = $ua->get($remote_url);

        return \$get_response->decoded_content if $get_response->is_success;
        die "Failed to retrieve data. Error: ", $get_response->status_line, "\n";
    }

    my $redis_conn = do_conn("127.0.0.1", 6379);
    my $network_cache_key = "ipc:hypertexts";
    my $cache_size = 1 << 10; # 1024 elements
    my $src_url = "https://httpbin.org/get";
    do_cache ($redis_conn, $network_cache_key, $cache_size, $src_url, sub { fetcher_http_get_method($src_url) });
    do_disconn($redis_conn);
}
