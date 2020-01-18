Name:           rpcbind
Version:        0.2.0
Release:        47%{?dist}
Summary:        Universal Addresses to RPC Program Number Mapper
Group:          System Environment/Daemons
License:        BSD
URL:            http://git.linux-nfs.org/?p=steved/rpcbind.git;a=summary

BuildRoot:      %{_tmppath}/%{name}-%{version}-root-%(%{__id_u} -n)
Source0:        http://downloads.sourceforge.net/rpcbind/%{name}-%{version}.tar.bz2
Source1: rpcbind.service
Source2: rpcbind.socket
Source3: rpcbind.sysconfig
Source4: rpcbind.conf

Patch001: rpcbind-0_2_1-rc4.patch
Patch002: rpcbind-0.2.0-warnings.patch
Patch003: rpcbind-0.2.0-rpcinfo-mantypo.patch
#
# RHEL7.2
#
Patch004: rpcbind-0.2.0-configure.ac.patch
Patch005: rpcbind-0.2.0-nss-altfiles.patch
Patch006: rpcbind-0.2.0-systemd-socket.patch
Patch007: rpcbind-0.2.0-good-term.patch
Patch008: rpcbind-0.2.0-warmstart-noerror.patch
#
# RHEL7.3
#
Patch009: rpcbind-0.2.0-CVE20157236-memcorrup.patch 
Patch010: rpcbind-0.2.0-debug.patch
#
# RHEL7.4
#
Patch011: rpcbind-0.2.0-xlog-warn.patch
Patch012: rpcbind-0.2.0-i-warn.patch
Patch013: rpcbind-0.2.0-memleaks.patch
Patch014: rpcbind-0.2.0-freeing-static-memory.patch


Requires: glibc-common setup
Requires: libtirpc >= 0.2.4-0.7
Conflicts: man-pages < 2.43-12
BuildRequires: automake, autoconf, libtool, systemd-units
BuildRequires: libtirpc-devel, quota-devel, tcp_wrappers-devel, systemd-devel
Requires(pre): coreutils shadow-utils
Requires(post): chkconfig systemd-units systemd-sysv
Requires(preun): systemd-units
Requires(postun): systemd-units coreutils

Provides: portmap = %{version}-%{release}
Obsoletes: portmap <= 4.0-65.3

%description
The rpcbind utility is a server that converts RPC program numbers into
universal addresses.  It must be running on the host to be able to make
RPC calls on a server on that machine.

%prep
%setup -q
%patch001 -p1
# 884165 - Package rpcbind-0.2.0-16.el7 failed RHEL7 RPMdiff testing
%patch002 -p1
# 963512 - Cmd rpcinfo usage info is not correct
%patch003 -p1
# 1171291 - Add nss-altfiles to rpcbind user lookup path
%patch004 -p1
%patch005 -p1
# 1203820 - First nfs mount command taking long time after every reboot
%patch006 -p1
# 1174653 - rpcbind does not shutdown cleanly 
%patch007 -p1
# 1227852 - rpcbind-0.2.0-27.el7 emits error messages after every reboot
%patch008 -p1
# 1283641 - CVE-2015-7236 rpcbind: Use-after-free vulnerability in PMAP_CALLIT
%patch009 -p1
# 1358890 - Enable upstream debugging
%patch010 -p1
# 1377531 - Compiler warning: implicit declaration of function 'xlog'....
%patch011 -p1
# 1377560 - Compiler warning: unused variable 'i' [-Wunused-variable]
%patch012 -p1
# 1449456 rpcbind: Memory leak when failing to parse XDR strings...
%patch013 -p1
# 1454876 - rpcbind crash on start
%patch014 -p1

%build
%ifarch s390 s390x
PIE="-fPIE"
%else
PIE="-fpie"
%endif
export PIE

RELRO="-Wl,-z,relro,-z,now"

RPCBUSR=rpc
RPCBDIR=/run/rpcbind
CFLAGS="`echo $RPM_OPT_FLAGS $ARCH_OPT_FLAGS $PIE $RELRO`"

autoreconf -fisv
%configure CFLAGS="$CFLAGS" LDFLAGS="-pie" \
    --enable-warmstarts \
    --with-statedir="$RPCBDIR" \
    --with-rpcuser="$RPCBUSR" \
    --with-nss-modules="files altfiles" \
    --enable-libwrap \
    --enable-debug

make all

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}{/sbin,/usr/sbin,/etc/sysconfig}
mkdir -p %{buildroot}%{_unitdir}
mkdir -p %{buildroot}%{_mandir}/man8
mkdir -p %{buildroot}%%{_prefix}/lib/tmpfiles.d/
mkdir -p %{buildroot}/var/lib/rpcbind
make DESTDIR=$RPM_BUILD_ROOT install

mv -f ${RPM_BUILD_ROOT}%{_bindir}/rpcbind ${RPM_BUILD_ROOT}%{_sbindir}
mv -f ${RPM_BUILD_ROOT}%{_bindir}/rpcinfo ${RPM_BUILD_ROOT}%{_sbindir}
install -m644 %{SOURCE1} %{buildroot}%{_unitdir}
install -m644 %{SOURCE2} %{buildroot}%{_unitdir}
install -m644 %{SOURCE3} %{buildroot}/etc/sysconfig/rpcbind
install -d -m 0755 %{buildroot}%{_prefix}/lib/tmpfiles.d/
install -m644 %{SOURCE4} %{buildroot}%{_prefix}/lib/tmpfiles.d/rpcbind.conf

%clean
rm -rf %{buildroot}

%pre

# Softly static allocate the rpc uid and gid.
getent group rpc >/dev/null || groupadd -f -g 32 -r rpc
if ! getent passwd rpc >/dev/null ; then
       if ! getent passwd 32 >/dev/null ; then
          useradd -l -c "Rpcbind Daemon" -d /var/lib/rpcbind  \
             -g rpc -M -s /sbin/nologin -o -u 32 rpc > /dev/null 2>&1
       else
          useradd -l -c "Rpcbind Daemon" -d /var/lib/rpcbind  \
             -g rpc -M -s /sbin/nologin rpc > /dev/null 2>&1
       fi
fi
%post
if [ $1 -eq 1 ] ; then 
    # Initial installation
    /bin/systemctl enable rpcbind.service >/dev/null 2>&1 || :
fi

%preun
if [ $1 -eq 0 ]; then
	# Package removal, not upgrade
	/bin/systemctl --no-reload disable rpcbind.service >/dev/null 2>&1 || :
	/bin/systemctl stop rpcbind.service >/dev/null 2>&1 || :
	rm -rf /var/lib/rpcbind
fi

%postun
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
if [ $1 -ge 1 ]; then
	# Package upgrade, not uninstall
	/bin/systemctl try-restart rpcbind.service >/dev/null 2>&1 || :
fi

%triggerun -- rpcbind < 0.2.0-15
%{_bindir}/systemd-sysv-convert --save rpcbind >/dev/null 2>&1 ||:
/bin/systemctl --no-reload enable rpcbind.service >/dev/null 2>&1
/sbin/chkconfig --del rpcbind >/dev/null 2>&1 || :
/bin/systemctl try-restart rpcbind.service >/dev/null 2>&1 || :

%triggerin -- rpcbind > 0.2.0-26
/bin/systemctl enable rpcbind.socket >/dev/null 2>&1 || :
/bin/systemctl restart rpcbind.socket >/dev/null 2>&1 || :

%triggerpostun -- rpcbind < -2.2.0-29
[ ! -d /run/rpcbind ] && mkdir /run/rpcbind || :
/usr/bin/chown rpc:rpc /run/rpcbind
[ -f /var/lib/rpcbind/rpcbind.xdr ] && \
	mv /var/lib/rpcbind/rpcbind.xdr /run/rpcbind || :
[ -f /var/lib/rpcbind/portmap.xdr ] && \
	mv /var/lib/rpcbind/portmap.xdr /run/rpcbind || :
[ -x /sbin/restorecon ] && /sbin/restorecon -R /run/rpcbind
/bin/systemctl try-restart nfs-server >/dev/null 2>&1 || :

%files
%defattr(-,root,root)
%config(noreplace) /etc/sysconfig/rpcbind
%doc AUTHORS ChangeLog README
%{_sbindir}/rpcbind
%{_sbindir}/rpcinfo
%{_mandir}/man8/*
%{_unitdir}/rpcbind.service
%{_unitdir}/rpcbind.socket
%{_prefix}/lib/tmpfiles.d/rpcbind.conf
%dir %attr(700,rpc,rpc) /var/lib/rpcbind

%changelog
* Sat Aug 25 2018 Steve Dickson <steved@redhat.com> - 0.2.0-47
- rpcbind.service: Not pulling the rpcbind.target (bz 1613210)

* Mon Aug 20 2018 Steve Dickson <steved@redhat.com> - 0.2.0-46
- Updated the upsteam URL (bz 1583921)

* Thu Apr 19 2018 Steve Dickson <steved@redhat.com> - 0.2.0-45
- Added back the ListenStream stanzas from rpcbind.socket (bz 1530721)

* Fri Jan  5 2018 Steve Dickson <steved@redhat.com> - 0.2.0-44
* Removed ListenStream stanzas from rpcbind.socket (bz 1425758)

* Wed Oct 25 2017 Steve Dickson <steved@redhat.com> - 0.2.0-43
- Updated rpcbind.service to upstream version (bz 1425663)

* Tue May 30 2017 Steve Dickson <steved@redhat.com> - 0.2.0-42
- Stop freeing static memory (bz 1454876)

* Wed May 17 2017 Steve Dickson <steved@redhat.com> - 0.2.0-41
- Fixed typo in memory leaks patch (bz 1449456)

* Thu May 11 2017 Steve Dickson <steved@redhat.com> - 0.2.0-40
- Fixed memory leaks (bz 1449456)

* Sat Feb 25 2017 Steve Dickson <steved@redhat.com> - 0.2.0-39
- Added libtirpc dependency (bz 1396291)
- Removed xlog warning (bz 1377531)
- Removed an 'i' warning (bz 1377560)

* Tue Aug  2 2016 Steve Dickson <steved@redhat.com> - 0.2.0-38
- Removing the braces from the ${RPCBIND_ARGS} in rpcbind.service (bz 1362232)

* Fri Jul 29 2016 Steve Dickson <steved@redhat.com> - 0.2.0-37
- Make sure rpcbind.socket listens for remote IPv6 connections (bz 1359592)

* Thu Jul 21 2016 Steve Dickson <steved@redhat.com> - 0.2.0-36
- Added upstream debugging (bz 1358890)

* Sat Apr  9 2016 Steve Dickson <steved@redhat.com> - 0.2.0-35
- Restart rpcbind.socket on restarts (bz 1303751)
- Added localhost:111 to rpcbind socket activation (bz 1293430)
- Soft static allocate rpc uid/gid (bz 1321279)

* Mon Nov 30 2015 Steve Dickson <steved@redhat.com> - 0.2.0-34
- Fix memory corruption in PMAP_CALLIT code (bz 1283641)

* Tue Oct 20 2015 Steve Dickson <steved@redhat.com> - 0.2.0-33
- More triggerpostu typos (bz 1272841)

* Fri Oct  2 2015 Steve Dickson <steved@redhat.com> - 0.2.0-32
- Fixed typo in triggerpostu (bz 1268139)

* Mon Sep 28 2015 Steve Dickson <steved@redhat.com> - 0.2.0-31
- Use systemd-tmpfiles to create the warmstart direcory (bz 1240817)

* Tue Sep 22 2015 Steve Dickson <steved@redhat.com> - 0.2.0-30
- Create the warmstart file with the correct uid/gid (bz 1240817)

* Thu Sep 10 2015 Steve Dickson <steved@redhat.com> - 0.2.0-29
- Change RPCBDIR to be /run since that will exist after a
  reboot and bindings wil be perserved during upgrades
  but not reboots. (bz 1240817)

* Thu Jul 30 2015 Steve Dickson <steved@redhat.com> - 0.2.0-28
- Remove error message on warmstart (bz 1227852)

* Mon May  4 2015 Steve Dickson <steved@redhat.com> - 0.2.0-27
- Add nss-altfiles to rpcbind user lookup path (bz 1171291)
- Add support for systemd socket activation (bz 1203820)
- Added a tmpfiles.d configuration (bz 1181779)
- Shutdown cleanly (bz 1174653)

* Sat Nov 15 2014 Steve Dickson <steved@redhat.com> - 0.2.0-26
- Moved rpcbind from /sbin to /usr/sbin (bz 1159683)

* Mon Sep 22 2014 Steve Dickson <steved@redhat.com> - 0.2.0-25
- Fixed some warnings in in6_fillscopeid() (bz 884165)
- Fixed typo in rpcinfo manpage (bz 963512)
- Removed unnecessary targets from rpcbind.service  (bz 1036791)

* Fri Sep 19 2014 Steve Dickson <steved@redhat.com> - 0.2.0-24
- Added the RELRO CFLAGS (bz 1092513)

* Fri Jan 24 2014 Daniel Mach <dmach@redhat.com> - 0.2.0-23
- Mass rebuild 2014-01-24

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 0.2.0-22
- Mass rebuild 2013-12-27

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.0-21
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Tue Oct 23 2012 Steve Dickson <steved@redhat.com> - 0.2.0-20
- Update to the latest upstream release: rpcbind-0_2_1-rc4 (bz 869365)

* Tue Oct 16 2012 Steve Dickson <steved@redhat.com> - 0.2.0-19
- Renamed RPCBINDOPTS to RPCBIND_ARGS for backward compatibility (bz 861025)

* Sun Oct 14 2012 Steve Dickson <steved@redhat.com> - 0.2.0-18
- Fixed typo causing rpcbind to run as root (bz 734598)
- Added /etc/sysconfig/rpcbind config file (bz 861025)

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.0-17
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.0-16
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Mon Sep 12 2011 Steve Dickson <steved@redhat.com> - 0.2.0-15
- Bumped up the tigger version to this version, 0.2.0-15 (bz 713574)

* Fri Sep  9 2011 Tom Callaway <spot@fedoraproject.org> - 0.2.0-14
- fix scriptlets to enable service by default

* Fri Jul  8 2011 Steve Dickson <steved@redhat.com> - 0.2.0-13
- Spec file clean up

* Thu Jul  7 2011 Steve Dickson <steved@redhat.com> - 0.2.0-12
- Migrated SysV initscripts to systemd (bz 713574)

* Thu Mar 17 2011 Steve Dickson <steved@redhat.com> - 0.2.0-11
- Updated to the latest upstream release: rpcbind-0_2_1-rc3

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.0-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon Dec 13 2010 Steve Dickson <steved@redhat.com> - 0.2.0-9
- Fixed an incorrect exit code for service rpcbind status (bz 662411)

* Tue Nov 30 2010 Steve Dickson <steved@redhat.com> - 0.2.0-8
- Updated to the latest upstream release: rpcbind-0.2.1-rc2

* Fri Jul 16 2010 Tom "spot" Callaway <tcallawa@redhat.com> - 0.2.0-7
- correct license tag to BSD

* Tue Jul 13 2010 Steve Dickson <steved@redhat.com> - 0.2.0-6
- Made initscript LSB compliant (bz 614193)
- Added no fork patch

* Tue Jul  6 2010 Steve Dickson <steved@redhat.com> - 0.2.0-5
- Set SO_REUSEADDR on listening sockets (bz 597356)

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2.0-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Mon Jul 06 2009 Adam Jackson <ajax@redhat.com> 0.2.0-3
- Requires(pre): coreutils for cut(1).

* Thu Jun 25 2009 Steve Dickson <steved@redhat.com> - 0.2.0-2
- Fixed pre scriptle failure during upgrades (bz 507364)
- Corrected the usage info to match what the rpcbind man
    page says. (bz 466332)
- Correct package issues (bz 503508)

* Fri May 29 2009 Steve Dickson <steved@redhat.com> - 0.2.0-1
- Updated to latest upstream release: 0.2.0

* Tue May 19 2009 Tom "spot" Callaway <tcallawa@redhat.com> - 0.1.7-3
- Replace the Sun RPC license with the BSD license, with the explicit permission of Sun Microsystems

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.1.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Wed Nov 19 2008 Steve Dickson <steved@redhat.com>  0.1.7-1
- Update to latest upstream release: 0.1.7

* Tue Sep 30 2008 Steve Dickson <steved@redhat.com>  0.1.6-3
- Fixed a typo in the rpcbind.init script that stop warm starts
  from happening with conrestarts
- Fixed scriptlet failure (bz 462533)

* Tue Sep 16 2008 Steve Dickson <steved@redhat.com> 0.1.6-2
- Added usptream patches 01 thru 03 that do:
    * Introduce helpers for ipprot/netid mapping
    * Change how we decide on the netids to use for portmap
    * Simplify port live check in pmap_svc.c

* Wed Jul  9 2008 Steve Dickson <steved@redhat.com> 0.1.6-1
- Updated to latest upstream release 0.1.6

* Wed Jul  2 2008 Steve Dickson <steved@redhat.com> 0.1.5-5
- Fixed SYNOPSIS section in the rpcinfo man page (bz 453729)

* Fri Jun 27 2008 Steve Dickson <steved@redhat.com> 0.1.5-4
- Removed the documentation about the non-existent 
  '-L' flag (bz 446915)

* Fri Jun 27 2008 Steve Dickson <steved@redhat.com> 0.1.5-3
- Set password and service lookups to be local (bz 447092)

* Mon Jun 23 2008 Steve Dickson <steved@redhat.com> 0.1.5-2
- rpcbind needs to downgrade to non-priviledgied group.

* Mon Jun 23 2008 Steve Dickson <steved@redhat.com> 0.1.5-1
- Updated to latest upstream release 0.1.5

* Mon Feb 11 2008 Steve Dickson <steved@redhat.com> 0.1.4-14
- Fixed a warning in pmap_svc.c
- Cleaned up warmstarts so uid are longer needed, also
  changed condrestarts to use warmstarts. (bz 428496)

* Thu Jan 24 2008 Steve Dickson <steved@redhat.com> 0.1.4-13
- Fixed connectivity with Mac OS clients by making sure handle_reply()
  sets the correct fromlen in its recvfrom() call (bz 244492)

* Mon Dec 17 2007 Steve Dickson <steved@redhat.com> 0.1.4-12
- Changed is_loopback() and check_access() see if the calling
  address is an address on a local interface, just not a loopback
  address (bz 358621).

* Wed Oct 17 2007 Steve Dickson <steved@redhat.com> 0.1.4-11
- Reworked logic in initscript so the correct exit is 
  used when networking does not exist or is set up
  incorrectly.

* Tue Oct 16 2007 Steve Dickson <steved@redhat.com> 0.1.4-10
- Corrected a typo in the initscript from previous 
  commit.

* Mon Oct 15 2007 Steve Dickson <steved@redhat.com> 0.1.4-9
- Fixed typo in Summary (bz 331811)
- Corrected init script (bz 247046)

* Sat Sep 15 2007 Steve Dickson <steved@redhat.com> 0.1.4-8
- Fixed typo in init script (bz 248285)
- Added autoconf rules to turn on secure host checking
  via libwrap. Also turned on host check by default (bz 248284)
- Changed init script to start service in runlevel 2 (bz 251568)
- Added a couple missing Requires(pre) (bz 247134)

* Fri May 25 2007 Steve Dickson <steved@redhat.com> 0.1.4-7
- Fixed condrestarts (bz 241332)

* Tue May 22 2007 Steve Dickson <steved@redhat.com> 0.1.4-6
- Fixed an ipv6 related segfault on startup (bz 240873)

* Wed Apr 18 2007 Steve Dickson <steved@redhat.com> 0.1.4-5
- Added dependency on setup which contains the correct
  rpcbind /etc/service entry which in turns stops 
  rpcbind from haning when NIS is enabled. (bz 236865)

* Wed Apr 11 2007 Jeremy Katz <katzj@redhat.com> - 0.1.4-4
- change man-pages requires into a conflicts as we don't have to have 
  man-pages installed, but if we do, we need the newer version

* Fri Apr  6 2007 Steve Dickson <steved@redhat.com> 0.1.4-3
- Fixed the Provides and Obsoletes statments to correctly
  obsolete the portmap package.
* Tue Apr  3 2007 Steve Dickson <steved@redhat.com> 0.1.4-2
- Added dependency on glibc-common which allows the
  rpcinfo command to be installed in the correct place.
- Added dependency on man-pages so the rpcinfo man 
  pages don't conflict.
- Added the creation of /var/lib/rpcbind which will be
  used to store state files.
- Make rpcbind run with the 'rpc' uid/gid when it exists.

* Wed Feb 21 2007 Steve Dickson <steved@redhat.com> 0.1.4-1
- Initial commit
- Spec reviewed (bz 228894)
- Added the Provides/Obsoletes which should
  cause rpcbind to replace portmapper
