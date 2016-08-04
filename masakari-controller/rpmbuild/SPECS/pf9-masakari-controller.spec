%define         project masakari
%define         summary OpenStack Masakari Services
%define         masakari-controller
%define         daemons controller
%define         _unpackaged_files_terminate_build 0 

Name:           pf9-%{project}
Version:        %{_version}
Release:        %{_release}.%{_githash}
Summary:        %{summary}

License:        Commercial
URL:            http://www.platform9.com

AutoReqProv:    no
Provides:       pf9-%{project}
BuildArch:      %{_arch}

BuildRequires:  python-devel
BuildRequires:  libffi-devel
BuildRequires:  mysql-devel
BuildRequires:  postgresql-devel

#Requires: python-lxml
Requires(pre): /usr/sbin/useradd, /usr/bin/getent
Requires(postun): /usr/sbin/userdel

%description
Platform9 distribution of the %{summary} built from pf9-%{project}@%{_githash}

%prep
# expand into BUILD
tar xf %{_sourcedir}/%{project}.tar

%build

%install

# virtualenv and setup
virtualenv %{buildroot}/opt/pf9/%{project}
%{buildroot}/opt/pf9/%{project}/bin/python setup.py install
%{buildroot}/opt/pf9/%{project}/bin/python %{buildroot}/opt/pf9/%{project}/bin/pip install .

# tests
rm -rf %{buildroot}/opt/pf9/%{project}/lib/python?.?/site-packages/%{project}/tests

# Known issue with pexpect with python 2.7
# https://github.com/pexpect/pexpect/issues/220
rm -f %{buildroot}/opt/pf9/%{project}/lib/python?.?/site-packages/pexpect/async.py

# systemd
install -d -m 755 %{buildroot}/etc/systemd/system/
install -p -m 664 etc/systemd/system/pf9-masakari-controller.service %{buildroot}/etc/systemd/system/

# config files
install -d -m 755 %{buildroot}%{_sysconfdir}/%{project}
install -p -m 640 -t %{buildroot}%{_sysconfdir}/%{project}/ \
                     etc/*.conf


# patch the #!python with the venv's python
sed -i "s/\#\!.*python/\#\!\/opt\/pf9\/%{project}\/bin\/python/" \
       %{buildroot}/opt/pf9/%{project}/bin/%{project}-*

# copy to /usr/bin
install -d -m 755 %{buildroot}%{_bindir}
install -p -m 755 -t %{buildroot}%{_bindir} \
                     %{buildroot}/opt/pf9/%{project}/bin/%{project}-*
 
# logrotate
install -p -D -m 640 etc/%{project}.logrotate \
                     %{buildroot}%{_sysconfdir}/logrotate.d/%{project}

# Setup directories
install -d -m 755 %{buildroot}%{_sharedstatedir}/masakari
install -d -m 755 %{buildroot}%{_sharedstatedir}/masakari/masakari-controller
install -d -m 755 %{buildroot}%{_sharedstatedir}/masakari/masakari-controller/db
install -d -m 755 %{buildroot}%{_sharedstatedir}/masakari/masakari-controller/controller

# log directory
install -d -m 755 %{buildroot}%{_localstatedir}/log/%{project}

# pid directory
install -d -m 755 %{buildroot}%{_localstatedir}/run/%{project}

%clean

%files
%defattr(-,%{project},%{project},-)

# the virtualenv
%dir /opt/pf9/%{project}
/opt/pf9/%{project}

# services
#%dir /etc/systemd/system/
/etc/systemd/system/pf9-masakari-controller.service

# /usr/bin
%{_bindir}/%{project}-*

# /etc/project config files
%dir %{_sysconfdir}/%{project}
%config(noreplace) %attr(-, root, %{project}) %{_sysconfdir}/%{project}/*.conf

# /var/lib 
%dir %attr(0755, %{project}, nobody) %{_sharedstatedir}/%{project}

# /var/log
%dir %attr(0755, %{project}, nobody) %{_localstatedir}/log/%{project}

# /var/run (for pidfile)
%dir %attr(0755, %{project}, nobody) %{_localstatedir}/run/%{project}

%pre
/usr/bin/getent group %{project} || \
    /usr/sbin/groupadd -r %{project}
/usr/bin/getent passwd %{project} || \
    /usr/sbin/useradd -r \
                      -d /opt/pf9/%{project} \
                      -s /sbin/nologin \
                      -g %{project} \
                      %{project}

%post
for daemon in %{daemons}
do
    chkconfig --add pf9-masakari-controller
done

%preun
if [ $1 = 0 ] ; then
    for daemon in %{daemons}
    do
        /sbin/service %{project}-$daemon stop >/dev/null 2>&1
        /sbin/chkconfig --del pf9-masakari-controller
    done
fi

%postun
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    for daemon in %{daemons}
    do
        /sbin/service pf9-masakari-controller condrestart > /dev/null 2>&1 || :
    done
else
    /usr/sbin/userdel %{project}
fi

%changelog
