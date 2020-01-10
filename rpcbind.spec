%{!?_initddir:%define _initddir /etc/rc.d/init.d}

Name:           rpcbind
Version:        0.2.0
Release:	    16%{?dist}
Summary:        Universal Addresses to RPC Program Number Mapper
Group:          System Environment/Daemons
License:        BSD
URL:            http://nfsv4.bullopensource.org

BuildRoot:      %{_tmppath}/%{name}-%{version}-root-%(%{__id_u} -n)
Source0:        http://downloads.sourceforge.net/rpcbind/%{name}-%{version}.tar.bz2
Source1: rpcbind.init

#
# RHEL6.3
#
Patch100: rpcbind-0.2.0-usage-fix.patch
Patch101: rpcbind-0.2.0-tpi-cots-reuseaddr.patch
Patch102: rpcbind-0.2.0-drop-sup-groups.patch
#
# RHEL6.4
#
Patch103: rpcbind-0.2.0-looback-permissive.patch
Patch104: rpcbind-0.2.0-manpage-updated.patch
Patch105: rpcbind-0.2.0-broadcast.patch
#
# RHEL6.8
#
Patch106: rpcbind-0.2.0-pmapcallit-memorycorp.patch
#
# RHEL6.10
#
Patch107: rpcbind-0.2.0-memleadks.patch
Patch108: rpcbind-0.2.0-freeing-static-memory.patch

Requires: glibc-common setup
Conflicts: man-pages < 2.43-12
BuildRequires: automake, autoconf, libtool
BuildRequires: libtirpc-devel, quota-devel, tcp_wrappers-devel
BuildRequires: libgssglue-devel
Requires(pre): /usr/sbin/groupadd
Requires(pre): /usr/sbin/useradd
Requires(pre): coreutils
Requires(post): /sbin/chkconfig
Requires(post): /sbin/chkconfig
Requires: libgssglue

Provides: portmap = %{version}-%{release}
Obsoletes: portmap <= 4.0-65.3

%description
The rpcbind utility is a server that converts RPC program numbers into
universal addresses.  It must be running on the host to be able to make
RPC calls on a server on that machine.

%prep
%setup -q
%patch100 -p1
%patch101 -p1

# 726954 - rpcbind should drop supplemental groups
%patch102 -p1
# 731542 - rpcbind without -i restricts set/unset to root user on localhost
%patch103 -p1
# 813898 - No rpcbind entry in section 3 of the man pages as mentioned in rpcbind man page
%patch104 -p1
# 864056 - RHEL6 rpcbind is "swallowing" broadcast RPC replies
%patch105 -p1
# 1186933 - rpcbind causes General Protection Fault
%patch106 -p1
# 1449464 - CVE-2017-8779 rpcbind: libtirpc, libntirpc: Memory leak...
%patch107 -p1
# 1455142 - rpcbind crash on start
%patch108 -p1

%build
%ifarch s390 s390x
PIE="-fPIE"
%else
PIE="-fpie"
%endif
export PIE

RPCBUSR=rpc
RPCBDIR=/var/cache/rpcbind
CFLAGS="`echo $RPM_OPT_FLAGS $ARCH_OPT_FLAGS $PIE`"

autoreconf -fisv
%configure CFLAGS="$CFLAGS" LDFLAGS="-pie" \
    --enable-warmstarts \
    --with-statedir="$RPCBDIR" \
    --with-rpcuser="$RPCBUSR" \
    --enable-libwrap \
    --enable-debug

make all


%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/sbin
mkdir -p %{buildroot}/usr/sbin
mkdir -p %{buildroot}%{_sysconfdir}/rc.d/init.d
mkdir -p %{buildroot}%{_mandir}/man8
mkdir -p %{buildroot}/var/cache/rpcbind

install -m 755 src/rpcbind ${RPM_BUILD_ROOT}/sbin
install -m 755 src/rpcinfo ${RPM_BUILD_ROOT}%{_sbindir}
install -m 644 man/rpcbind.8 ${RPM_BUILD_ROOT}%{_mandir}/man8
install -m 644 man/rpcinfo.8 ${RPM_BUILD_ROOT}%{_mandir}/man8
install -m 755 ${RPM_SOURCE_DIR}/rpcbind.init ${RPM_BUILD_ROOT}%{_initddir}/rpcbind

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
/sbin/chkconfig --add %{name}

%preun
if [ $1 -eq 0 ]; then
    service rpcbind stop > /dev/null 2>&1
    /sbin/chkconfig --del %{name}
	rm -rf /var/cache/rpcbind
fi
%postun
if [ "$1" -ge "1" ]; then
    service rpcbind condrestart > /dev/null 2>&1
fi

%files
%defattr(-,root,root)
%doc AUTHORS ChangeLog README
/sbin/rpcbind
%{_sbindir}/rpcinfo
%{_mandir}/man8/*
%config %{_initddir}/rpcbind

%dir %attr(700,rpc,rpc) /var/cache/rpcbind

%changelog
* Thu Feb  8 2018 Steve Dickson <steved@redhat.com> - 0.2.0-16
- Changed the license tag to BSD (bz 1336558)

* Tue May 30 2017 Steve Dickson <steved@redhat.com> - 0.2.0-15
- Stop freeing static memory (bz 1455142)

* Thu May 18 2017 Steve Dickson <steved@redhat.com> - 0.2.0-14
- Fix for CVE-2017-8779 (bz 1449464)

* Mon Jun 27 2016 Steve Dickson <steved@redhat.com> - 0.2.0-13
- Soft static allocate rpc uid/gid (bz 1300533)

* Fri Nov 13 2015 Steve Dickson <steved@redhat.com> - 0.2.0-12
- Fix memory corruption in PMAP_CALLIT code (bz 1186933)

* Tue Oct 23 2012 Steve Dickson <steved@redhat.com> - 0.2.0-11
- Stop rpcbind from "swallowing" broadcast RPC replies (bz 864056)

* Mon Aug 20 2012 Steve Dickson <steved@redhat.com> - 0.2.0-10
- Make is_loopback check more permissive (bz 731542)
- Removed the rpcbind(3) reference in the man page (bz 813898)

* Thu Mar  8 2012 Steve Dickson <steved@redhat.com> - 0.2.0-9
- Drop supplemental groups (bz 726954)

* Mon Aug 16 2010 Steve Dickson <steved@redhat.com> - 0.2.0-8
- Moved caching files to /var/cache (bz 599705)

* Thu Jul 15 2010 Steve Dickson <steved@redhat.com> - 0.2.0-7
- More initscript LSB compliant updates (bz 578415)

* Tue Jul 13 2010 Steve Dickson <steved@redhat.com> - 0.2.0-6
- Made initscript LSB compliant (bz 578415)

* Thu Jun 03 2010 Jeff Layton <jlayton@redhat.com> - 0.2.0-5
- set SO_REUSEADDR on NC_TPI_COTS sockets (bz 597356)

* Mon Nov 30 2009 Dennis Gregorovic <dgregor@redhat.com> - 0.2.0-4.1
- Rebuilt for RHEL 6

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
