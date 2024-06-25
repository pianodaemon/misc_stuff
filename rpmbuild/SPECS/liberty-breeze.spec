Name:           liberty-breeze
Version:        24.0.0.6
Release:        1%{?dist}
Summary:        IBM WebSphere Liberty Application Server

License:        IBM
URL:            https://www.ibm.com/cloud/websphere-liberty
Source0:        wlp-webProfile8-24.0.0.6.zip

BuildArch:      noarch

%global solution_group susers
%global appserver_user wsuser

%description
IBM WebSphere Liberty is a fast, dynamic, and easy-to-use application server. It is designed to support rapid development and deployment of web and cloud-based applications.

%pre
# It verifies existance of the application linux server group
if ! getent group %{solution_group} >/dev/null 2>&1; then
    echo "Error: The '%{solution_group}' group does not exist."
    exit 1
fi

# It verifies existance of the application linux server user
if ! id -u %{appserver_user} >/dev/null 2>&1; then
    echo "Error: The '%{appserver_user}' user does not exist."
    exit 1
fi

%prep

%build
# No build steps required

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/opt/yield
unzip %{SOURCE0} -d %{buildroot}/opt/yield
mv %{buildroot}/opt/yield/wlp %{buildroot}/opt/wlp

# The yield is no longer required
rmdir %{buildroot}/opt/yield

%post
# Seting up ownership
chown -R %{appserver_user}:%{solution_group} /opt/wlp

%postun


%files
/opt/wlp

%changelog
* Thu Jun 20 2024 Your Name <negas@donmaquila.com> - 24.0.0.6-1
- Initial package
