%define         project masakari
%define         summary OpenStack Masakari Services
%define         daemons api engine
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

# tests
rm -rf %{buildroot}/opt/pf9/%{project}/lib/python2.?/site-packages/%{project}/tests

# init scripts
for daemon in %{daemons}
do
    initscript=%{buildroot}/%{_initrddir}/openstack-%{project}-$daemon
    install -p -D -m 755 etc/initd.template $initscript
    sed -i "s/suffix=.*/suffix=$daemon/" $initscript
done

# virtualenv and setup
virtualenv %{buildroot}/opt/pf9/%{project}
%{buildroot}/opt/pf9/%{project}/bin/python setup.py install
%{buildroot}/opt/pf9/%{project}/bin/python %{buildroot}/opt/pf9/%{project}/bin/pip install .

# Known issue with pexpect with python 2.7
# https://github.com/pexpect/pexpect/issues/220
rm -f %{buildroot}/opt/pf9/%{project}/lib/python?.?/site-packages/pexpect/async.py

# config files
install -d -m 755 %{buildroot}%{_sysconfdir}/%{project}
install -p -m 640 -t %{buildroot}%{_sysconfdir}/%{project}/ \
                     etc/masakari/*.conf etc/masakari/*.ini etc/masakari/*.json


# patch the #!python with the venv's python
sed -i "s/\#\!.*python/\#\!\/opt\/pf9\/%{project}\/bin\/python/" \
       %{buildroot}/opt/pf9/%{project}/bin/%{project}-*

# copy to /usr/bin
install -d -m 755 %{buildroot}%{_bindir}
install -p -m 755 -t %{buildroot}%{_bindir} \
                     %{buildroot}/opt/pf9/%{project}/bin/%{project}-*
 
# logrotate
install -p -D -m 640 etc/%{project}.logrotate \
                     %{buildroot}%{_sysconfdir}/logrotate.d/openstack-%{project}

# Setup directories
install -d -m 755 %{buildroot}%{_sharedstatedir}/masakari


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
%{_initrddir}/openstack-%{project}-*

# /usr/bin
%{_bindir}/%{project}-*

# /etc/project config files
%dir %{_sysconfdir}/%{project}
%config(noreplace) %attr(-, root, %{project}) %{_sysconfdir}/%{project}/*.conf
%config(noreplace) %attr(-, root, %{project}) %{_sysconfdir}/%{project}/*.ini
%config(noreplace) %attr(-, root, %{project}) %{_sysconfdir}/%{project}/*.json

# logrotate config
%{_sysconfdir}/logrotate.d/openstack-%{project}
%attr(0644, root, %{project}) %{_sysconfdir}/logrotate.d/openstack-%{project}

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
    chkconfig --add pf9-masakari-$daemon
done

%preun
if [ $1 = 0 ] ; then
    for daemon in %{daemons}
    do
        /sbin/service %{project}-$daemon stop >/dev/null 2>&1
        /sbin/chkconfig --del pf9-masakari-$daemon
    done
fi

%postun
if [ $1 -ge 1 ] ; then
    # Package upgrade, not uninstall
    for daemon in %{daemons}
    do
        /sbin/service pf9-masakari-$daemon condrestart > /dev/null 2>&1 || :
    done
else
    /usr/sbin/userdel %{project}
fi

%changelog
