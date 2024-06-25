Name:           jdk-breeze
Version:        11.0.23
Release:        1%{?dist}
Summary:        Java SE Development Kit 11.0.23

License:        Oracle Technology Network License Agreement for Oracle Java SE
URL:            https://www.oracle.com/downloads/licenses/javase-license1.html
Source0:        jdk-11.0.23_linux-x64_bin.tar.gz

BuildArch:      x86_64


%description
Java SE Development Kit

%pre


%prep


%build
# No build steps required

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/opt/yield
tar -xvzf %{SOURCE0} -C %{buildroot}/opt/yield
mv %{buildroot}/opt/yield/jdk-11.0.23 %{buildroot}/opt/jdk

# The yield is no longer required
rmdir %{buildroot}/opt/yield

# Create the script to set JAVA_HOME and PATH
mkdir -p %{buildroot}/etc/profile.d
echo '#!/bin/bash' > %{buildroot}/etc/profile.d/jdk-breeze.sh
echo 'export JDK_BREEZE=/opt/jdk' >> %{buildroot}/etc/profile.d/jdk-breeze.sh
echo 'export JAVA_HOME=$JDK_BREEZE' >> %{buildroot}/etc/profile.d/jdk-breeze.sh
echo 'export PATH=$JAVA_HOME/bin:$PATH' >> %{buildroot}/etc/profile.d/jdk-breeze.sh

%post

# It adds the jdk into the alternatives
update-alternatives --install /usr/bin/java java /opt/jdk/bin/java 1
update-alternatives --install /usr/bin/javac javac /opt/jdk/bin/javac 1
update-alternatives --install /usr/bin/jar jar /opt/jdk/bin/jar 1
update-alternatives --install /usr/bin/jshell jshell /opt/jdk/bin/jshell 1

# It turns this jdk into default alternative
update-alternatives --set java /opt/jdk/bin/java
update-alternatives --set javac /opt/jdk/bin/javac
update-alternatives --set jar /opt/jdk/bin/jar
update-alternatives --set jshell /opt/jdk/bin/jshell

# Updates the environment for all the users
source /etc/profile

%postun

update-alternatives --remove java /opt/jdk/bin/java
update-alternatives --remove javac /opt/jdk/bin/javac
update-alternatives --remove jar /opt/jdk/bin/jar
update-alternatives --remove jshell /opt/jdk/bin/jshell

source /etc/profile

%files
/opt/jdk
/etc/profile.d/jdk-breeze.sh

%changelog
* Thu Jun 20 2024 Your Name <negas@donmaquila.com> - 24.0.0.6-1
- Initial package
