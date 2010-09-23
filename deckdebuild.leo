<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet ekr_test?>
<leo_file>
<leo_header file_format="2" tnodes="0" max_tnode_index="5" clone_windows="0"/>
<globals body_outline_ratio="0.325830653805">
	<global_window_position top="0" left="549" height="933" width="719"/>
	<global_log_window_position top="0" left="0" height="0" width="0"/>
</globals>
<preferences/>
<find_panel_settings/>
<vnodes>
<v t="zaril.20100919105245" a="E"><vh>Project</vh>
<v t="zaril.20100919105245.1"><vh>research</vh>
<v t="zaril.20100919105245.2"><vh>explore sbuild</vh></v>
<v t="zaril.20100919105245.3"><vh>explore pbuilder</vh></v>
<v t="zaril.20100919105245.4"><vh>explore gdebi</vh></v>
</v>
<v t="zaril.20100919105245.5" a="E"><vh>design</vh></v>
<v t="zaril.20100919105427" a="E"><vh>implementation</vh>
<v t="zaril.20100919123407" a="E"><vh>setup a build chroot</vh>
<v t="zaril.20100919172841"><vh>most common build dependencies</vh></v>
</v>
<v t="zaril.20100919135234" a="M"><vh>perform build manually</vh></v>
<v t="zaril.20100919180049" a="M"><vh>cli code</vh></v>
<v t="zaril.20100920101348" a="M"><vh>build package</vh></v>
<v t="zaril.20100923030828" a="M"><vh>destroy deck unless build fails or requested</vh></v>
<v t="zaril.20100923031435" a="MTV"><vh>run as suid</vh></v>
</v>
</v>
</vnodes>
<tnodes>
<t tx="zaril.20100919105245">@nocolor
</t>
<t tx="zaril.20100919105245.1">* SUMMARY
types of build package relationships
    Build-Depends
    Build-Conflicts
    
    Build-Depends-Indep
    build-Conflicts-Indep

pbuilder-satisfydepends does what we want
    works from out of the chroot
    handles build-depends, build-depends-indep, build-conflicts and build-conflicts-indep
        
dpkg-checkbuilddeps
    check build dependencies and conflicts
        we don't actually need this if satisfydepends succeeds

three versions of pbuilder-satisfydepends in Ubuntu
    experimental
    gdebi

usage of satisfydepends
    cd /path/to/package
    /usr/lib/pbuilder/pbuilder-satisfydepends
        installs build-dependencies
            doesn't check if they already exist

    works from Gentoo (with --chroot)
        gdebi on the other hand, wouldn't be installed
  
Virtual packages
    virtual packages only exists logically
        name describes common functionality (multiple implementations of awk)
    list of virtual package names
    new packages must use virtual package names where apropriate
    examples
        awk
        c-shell
        c-compiler
        java-compiler
    /usr/share/doc/debian-policy/virtual-package-names-list.txt.gz

tweak virtual package selections by installing a package that provides the dependency to the build root
    no need for stupid tables

* QUESTIONS
Q: how does pbuilder resolve build dependencies?
A: with pbuilder-satisfydepends
---
Q: do we debuilding from the source directory or do we only build source packages? or both?
A: we build from source directory - this way we don't have to create tarballs
    sometimes creating tarballs is not an option
---
Q: does debuild clean the environment first?
A: yes
---
A: we debuild directly from the source directory, otherwise we have to create the source tarball
    and thats not always possible
---
Q: should we make package build configurable?
A:
    we could just fix any packages that don't build with fakeroot for whatever reason

* RANDOM IDEAS
    get apt to build-dep our package? 
        add our package Source to its database somehow?

    write a specialized program of our own to resolve build dependencies?

    compile with dpkg-buildpackage

    show shell commands we are performing to allow user to manually reproduce them

    modify sbuild?

    if we add a source to apt cache, specify which package to query 

    allow arbitrary satisfydepends program
        defaults to pbuilder's

* ABANDONED QUESTIONS
Q: does python-apt include code that makes resolving dependency versions easier?
Q: how does sbuild install them?
Q: how do we get apt-get to install them for an arbitrary source package?
Q: how do we add get APT to build-dep our package?

* RESOURCE: file:///home/z/docs/debian/www.us.debian.org/doc/debian-policy/ch-relationships.html#s-sourcebinarydeps
</t>
<t tx="zaril.20100919105245.2">Q: how does sbuild extract build dependencies?

it extracts Build-Depends Build-Depends-Indep Build-Conflicts and Build-Conflicts-Indep from the dsc
writes them to debian/.sbuild-build-deps

extracts Architecture

it applies a global table to those dependencies

    negative dependencies (I.e., conflicts) marked with "!"

filters missing deps that are essential
if deps are virtual packages, replaces them with alternatives over all provided packages

it uses dpkg --set-selections to install packages

after tha it removes the installed debs

DEBIAN_FRONTEND = "noninteractive"

</t>
<t tx="zaril.20100919105245.3">* SUMMARY
three versions of pbuilder-satisfydepends in Ubuntu
    experimental
    gdebi

usage of satisfydepends
    cd /path/to/package
    /usr/lib/pbuilder/pbuilder-satisfydepends
        installs build-dependencies
            doesn't check if they already exist

    works from Gentoo (with --chroot)
        gdebi on the other hand, wouldn't be installed
  
Virtual packages
    virtual packages only exists logically
        name describes common functionality (multiple implementations of awk)
    list of virtual package names
    new packages must use virtual package names where apropriate
    examples
        awk
        c-shell
        c-compiler
        java-compiler
    /usr/share/doc/debian-policy/virtual-package-names-list.txt.gz

tweak virtual package selections by installing a package that provides the dependency to the build root
    no need for stupid tables

how satisfydepends works

default
    uses apt-cache to get the cached package version and check if it satisfies the dependency
        uses dpkg --compare-versions "$PACKAGEVERSION" "$COMPARESTRING" "$DEPSVERSION"

    resolves build dependencies by simulating apt-get
        if it doesn't work, it assumes the package is virtual and tries to find a matching Provides in the apt cache
            apt-cache showpkg &lt;virtual-package&gt;
            if multiple provides exists: selects the last

        if any build dependency can not be satisfied, errors out

     this way a list of packages to install is created
        installed with apt-get -u --force-yes install &lt;package list&gt;


    removes conflicting build-depends if they exist

gdebi (written by Michael Vogt- knows what hes doing)
        
     INSTALL=$(/usr/bin/gdebi --quiet --apt-line --root $CHROOT $DEBIAN_CONTROL)
$CHROOTEXEC /usr/bin/apt-get install -y $INSTALL</t>
<t tx="zaril.20100919105245.4">features
    written in python
    has a GUI frontend
    capable of resolving dependencies of packages that are not part of the archive
</t>
<t tx="zaril.20100919105245.5">* DEPENDENCIES
pbuilder
deck

* CLI SYNTAX
deckdebuild [ -options ] /path/to/chroot
    -p --preserve-build
        DECKDEBUILD_PRESERVE_BUILD=0

    -u --user &lt;username&gt;
        DECKDEBUILD_USER="build"

    -r --root-cmd &lt;rootcmd&gt;
        DECKDEBUILD_ROOT_CMD="fakeroot"

    --satisfydepends-cmd /path/to/prog
        DECKDEBUILD_SATISFYDEPENDS_CMD=/usr/lib/pbuilder/pbuilder-satisfydepends

* IDEAS
show commands executed
    so user can reconstruct commands manually in case of error

don't use fakeroot? (doesn't matter anyhow?)

clean environment before chrooting?
    so we don't get weird locale errors

make deckdebuild suid?
    if chroot is unescapable then this is secure if we don't allow satisfydepends-cmd
        or maybe we only allow satisfydepends-cmd when not run suid

    we can additionally restrict who is allowed to execute via group execution privileges

* LOGIC  
data flow
    input: package source directory
    output: 
        binary debs
        &lt;package-source-name&gt;.build

export DEBIAN_FRONTEND="noninteractive"
    
parse options
    option precedence
        cli option
        environment
        built-in default       

check that we are running as root (we need root privileges)

deck the build root
install the build dependencies
    /usr/lib/pbuilder/pbuilder-satisfydepends --chroot /path/to/build/root
        installs build-dependencies
            doesn't check if they already exist

if build user doesn't exist create a build user
copy the package over to the build user's home
build the package with dpkg-buildpackage under fakeroot
    fakeroot dpkg-buildpackage -rfakeroot -uc -us -b

if the build fails, raise an exception?
if the build succeeds put the packages in the parent directory of the source package + build log

unless -p, we delete the deck environment the package was built in

* FILE STRUCTURE
/var/lib/deckdebuild

    chroots/&lt;package&gt;
        /home/&lt;user&gt;/&lt;package&gt;

    builds/&lt;package&gt; -&gt; ../chroots/&lt;package&gt;/home/&lt;user&gt;/&lt;package&gt;
</t>
<t tx="zaril.20100919105427">roadmap
    perform package build manually
    cli code
    save build log
    destroy deck
    suid stuff
        no satisfydepends
        path should be set

    

</t>
<t tx="zaril.20100919123407">location
    /turnkey/fab/buildroots
        e.g., /turnkey/fab/buildroots/jaunty

has to be a real directory, not a deck

do we have to mount proc and devpts and such?
    lets start without it - if we have to, then we'll add some default code

    the pbuilder default
        USEPROC=yes
        USEDEVPTS=yes
        USEDEVFS=no
        
configuration after debootstrap
    point sources.list to the proxy (127.0.0.1:9999)
    apt-get install fakeroot build-essential debhelper cdbs dpatch autotools-dev

install most common build dependencies

build depedencies virtual packages
    if you have preferences for virtual packages - install them yourself

gotcha
    LOCALE warnings from perl
        reason is LANG="en_GB" setting
            if we clean environment prior to chroot we won't have this problem
                or just clean LANG

    </t>
<t tx="zaril.20100919135234">mkdir -p /var/lib/deckdebuild/{chroots,builds}/hello-debhelper
deck /turnkey/fab/buildroots/jaunty/ /var/lib/deckdebuild/chroots/hello-debhelper/

# satisfy dependencies
/usr/lib/pbuilder/pbuilder-satisfydepends --chroot &lt;chroot&gt;

# check if user exists
getenv passwd &lt;username&gt; # from libc6 package~
    exists: prints password entry and returns exitcode == 0
    else: doesn't print anything, exitcode == 2    

    alternative
        grep -q ^&lt;username&gt;: /etc/passwd

# add user
useradd -m &lt;username&gt; # useradd is from the passwd package
    alternatives
        adduser (adduser package) 
            is an interactive perl program
        
    if user already exists prints
        useradd: user &lt;username&gt; exists # to stderr
        exitcode == 9

# delete any remnants
chroot &lt;chroot&gt; su &lt;username&gt; -l -c "rm -rf &lt;package-basename&gt;"

# copy package to chroot
tar -C ../ -cvf - $(basename $(pwd)) | chroot &lt;chroot&gt; su &lt;username&gt; -l -c "tar -xvf -"

# setup link in /var/lib/deckdebuild/builds

# perform build
chroot $c su &lt;username&gt; -l -c "cd hello-debhelper-2.1.1; dpkg-buildpackage -rfakeroot -uc -us -b"
    successful build: exitcode = 1

# get home directory
HOMEDIR=$(chroot &lt;chroot&gt; su build -l -c pwd)

cp &lt;chroot&gt;/$HOMEDIR/*.deb ../ # owned by invoking user

deck -D /var/lib/deckdebuild/chroots/&lt;package&gt;

</t>
<t tx="zaril.20100919172841">cat /var/lib/apt/lists/*Sources | 
    grep-dctrl -n -s Build-Depends  ""| 
    perl -pe 's/\s*[,\|]\s*/\n/g' | 
    perl -pe 's/\s*\(.*//; s/^\s*//; s/\[.*//' | sort | uniq -c |sort -n -r

  10257 debhelper
   2157 cdbs
   1338 dpatch
   1330 autotools-dev
    850 libx11-dev
    736 libgtk2.0-dev
    597 pkg-config
    591 zlib1g-dev
    488 autoconf
    477 gettext

    458 libxt-dev
    449 libncurses5-dev
    437 perl
    397 flex
    394 bison
    390 libtool
    381 libglib2.0-dev
    375 libxext-dev
    355 quilt
    344 libxml2-dev
    324 po-debconf
    323 x-dev
    322 kdelibs4-dev

    316 automake1.9
    306 python-all-dev
    290 libssl-dev
    265 python-central
    260 libxpm-dev
    258 libxml-parser-perl
    246 texinfo
    241 python-support
    241 python-dev
    237 libpng12-dev
    236 libgnomeui-dev
    234 libsdl1.2-dev
    233 libgtk1.2-dev
    227 libreadline5-dev
    221 dpkg-dev
    218 xutils
    218 libjpeg62-dev
    205 libglade2-dev
    204 docbook-to-man
    202 libqt3-mt-dev
    178 intltool
    175 libxmu-dev
    172 libxaw7-dev</t>
<t tx="zaril.20100919180049">* CLI SYNTAX
deckdebuild [ -options ] /path/to/chroot
    -p --preserve-build
        DECKDEBUILD_PRESERVE_BUILD=0

    -u --user &lt;username&gt;
        DECKDEBUILD_USER="build"

    -r --root-cmd &lt;rootcmd&gt;
        DECKDEBUILD_ROOT_CMD="fakeroot"

    --satisfydepends-cmd /path/to/prog
        DECKDEBUILD_SATISFYDEPENDS_CMD=/usr/lib/pbuilder/pbuilder-satisfydepends

</t>
<t tx="zaril.20100920101348">LOGIC
    see manual build`

Q: how do I identify packages?
A:
parse the control file and grab the names of all packages that are supposed to be built
    copy any deb that starts with &lt;package&gt;_

alternatives
    copy all debs
    parse the changes file and copy only the debs

</t>
<t tx="zaril.20100923030828"></t>
<t tx="zaril.20100923031435">logic
    no satisfydepends should be allowed to set in suid mode
    files should be copied as user
        parent directory should be writeable by invoking user
            e.g., don't write to directory owned by root



    </t>
</tnodes>
</leo_file>
