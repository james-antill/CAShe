%define auto_sitelib 1

%if %{auto_sitelib}
%{!?python_sitelib: %define python_sitelib %(python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%else
%define python_sitelib /usr/lib/python?.?/site-packages
%endif

# Sigh ... also see commit in Makefile
# 1549852fd1c2805ba6329309f97d11190c37256e = 0.99.2
%global gitname CAShe
%global commit 1549852fd1c2805ba6329309f97d11190c37256e
%global shortcommit %(c=%{commit}; echo ${c:0:7})

Summary: CAS (Content Addressable Storage) cache for your data/caches
Name: cashe
Version: 0.99.2
Release: 1%{dist}
License: LGPLv2+
URL: https://github.com/james-antill/CAShe
Source0: https://github.com/james-antill/%{gitname}/archive/%{commit}/%{gitname}-%{commit}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
BuildRequires: python
BuildRequires: python2-devel
BuildRequires: libxslt docbook-dtds docbook-style-xsl docbook-style-dsssl
# CheckRequires
BuildRequires: python-nose
# Not sure how far back
Requires: python >= 2.4
Requires: python-cashe = %{version}-%{release}
Provides: %{gitname} = %{version}
BuildArchitectures: noarch

%description
CAShe is a CAS (Content Addressable Storage) cache for your data/caches.
Everything that is stored in the CAShe can be deleted at any time, although
that will mainly happen when cleanup operations are called or on failures.

%package -n python-cashe
Summary: Python module for CAShe
# Not sure how far back
Requires: python >= 2.4

%description -n python-cashe
CAShe is a CAS (Content Addressable Storage) cache for your data/caches.
Everything that is stored in the CAShe can be deleted at any time, although
that will mainly happen when cleanup operations are called or on failures.

%prep
%setup -qn %{gitname}-%{commit}

%build
make

%check
make check

%install
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT
make DESTDIR=$RPM_BUILD_ROOT install
mkdir -p $RPM_BUILD_ROOT/var/cache/CAShe

# Ghost files ftw...
touch $RPM_BUILD_ROOT/var/cache/CAShe/config
mkdir $RPM_BUILD_ROOT/var/cache/CAShe/md5
mkdir $RPM_BUILD_ROOT/var/cache/CAShe/sha1
mkdir $RPM_BUILD_ROOT/var/cache/CAShe/sha256
mkdir $RPM_BUILD_ROOT/var/cache/CAShe/sha512

%clean
rm -rf $RPM_BUILD_ROOT


%files -n python-cashe
%defattr(-,root,root,-)
%license LICENSE
%doc README.md AUTHORS TODO DESIGN.md
%{python_sitelib}/cashe
%dir /var/cache/CAShe
%ghost /var/cache/CAShe/config
%ghost /var/cache/CAShe/md5
%ghost /var/cache/CAShe/sha1
%ghost /var/cache/CAShe/sha256
%ghost /var/cache/CAShe/sha512

%files
%{_mandir}/man*/cashe.*
%{_bindir}/cashe


%changelog
* Tue May 19 2015 James Antill <james@and.org> - 0.99.2-1
- Tweaks for Fedora policy review.

* Wed Feb 25 2015 James Antill <james@and.org> - 0.99-1
- Initial build.

