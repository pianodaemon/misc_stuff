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
        $debug and printf STDOUT "_boolean_action_handler [%s] -> %s %s returning %s\n", $redis_command, $key, "$elem" ,$res;
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
        $debug and printf STDOUT "_reserve_bloom_filter [BF.RESERVE] -> %s %s %s returning %s\n", $key, $error_rate, $capacity, $res;
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
        $debug and print STDOUT "Recovering share memory segment with key $shm_mem_key\n";
        return \@actions;
    }

    printf STDERR "Non-available share memory segment featuring key: $shm_mem_key\n";

    if (eval { _reserve_bloom_filter($redis_conn, $shm_mem_key, "0.01", "$shm_mem_size"); 1 }) {
        $debug and print STDOUT "Setting up share memory segment with key $shm_mem_key\n";
        return \@actions;
    } else {
        $debug and printf STDERR "%s\n", $@ || 'Unknown failure';
        die "Not possible to harness a share memory segment with key $shm_mem_key\n";
    }
}

sub _retrieve_record {
    my ($file_path, $ttl_expected) = @_;
    my $file_stat = stat($file_path) or die "Failed to retrieve cache record $file_path: $!\n";

    if (time - $file_stat->mtime > $ttl_expected) {
        unlink $file_path;
        die "Cache record has expired.\n";
    }

    $debug and print STDOUT "Asking for content via cache\n";
    return retrieve($file_path);
}

sub _obtain_from_icss {
    my ($shared_ref, $kcache, $fetch_handler) = @_;
    my $kfpath = $kcache . ".cache";
    my $do_registration = sub {
        nstore($fetch_handler->(), $kfpath);
        return;
    };

    my $register_and_retrieve = sub {
        my $sref;
        my $retrieved = 0;

        while (!$retrieved) {
            unless (eval {
                $sref = _retrieve_record($kfpath, 30);
                1;
            }) {
                $debug and printf STDERR "%s\n", $@ || 'Unknown failure';
                &$do_registration();
            } else {
                $retrieved = 1;
            }
        }

        return $sref;
    };

    my $found_flag = $shared_ref->[BF_CHECK]->($kcache);
    unless ($found_flag == 1) {
        &$do_registration();
        $shared_ref->[BF_ADD]->($kcache);
    }

    return $register_and_retrieve->();
}

sub ping {
    my ($redis_conn) = @_;

    my $pong = $redis_conn->db->ping;
    die "Failed to ping Redis server" unless $pong eq 'PONG';
    print STDOUT "Successfully pinged Redis server: $pong\n";
}

sub do_conn {
    my ($host, $port) = @_;

    # Resource Acquisition Is Initialization or RAII
    Mojo::IOLoop->start unless Mojo::IOLoop->is_running;
    my $redis_conn = Mojo::Redis->new("redis://$host:$port/0")->encoding("UTF-8");
    $debug and ping($redis_conn);
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
    return _obtain_from_icss($shared_ref, murmur32($src_url), $fetch_handler);
}


# From this point onward it is mostly explanatory regarding its correct usage.
{
    use LWP::UserAgent;
    sub fetcher_http_get_method {
        my $remote_url = shift;
        my $ua = LWP::UserAgent->new;

        print STDOUT "Asking for remote content via HTTP GET\n";
        my $get_response = $ua->get($remote_url);

        return \$get_response->decoded_content if $get_response->is_success;
        die "Failed to retrieve data. Error: ", $get_response->status_line, "\n";
    }

    my $redis_conn = do_conn("127.0.0.1", 6379);
    my $network_cache_key = "ipc:hypertexts";
    my $cache_size = 1 << 10; # 1024 elements
    my $src_url = "https://httpbin.org/get";
    my $sref = do_cache($redis_conn, $network_cache_key, $cache_size, $src_url, sub { fetcher_http_get_method($src_url) });
    print $$sref;
    do_disconn($redis_conn);
}
