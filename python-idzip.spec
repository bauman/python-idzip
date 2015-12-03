%define name python-idzip
%define version 0.1
%define unmangled_version 0.1
%define unmangled_version 0.1
%define release 1

Summary: Seekable, gzip compatible, compression format
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{unmangled_version}.tar.gz
Source1: idzip.bin
License: MIT
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: dan bauman <bauman.85@osu.edu>

%package cli
Summary: Client tools for idzip


%description
Seekable, gzip compatible, compression format

%description cli
Execute idzip from shell


%prep
%setup -n %{name}-%{unmangled_version} -n %{name}-%{unmangled_version}
cp -fp %{SOURCE1} ./


%build
python setup.py build

%install
python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES
mkdir -p $RPM_BUILD_ROOT/%{_bindir}
install -m 555 -p $RPM_BUILD_DIR/%{name}-%{version}/idzip.bin  $RPM_BUILD_ROOT/%{_bindir}/idzip

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)


%files cli
%{_bindir}/idzip

