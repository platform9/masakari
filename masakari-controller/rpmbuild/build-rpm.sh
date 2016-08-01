#!/bin/bash -x

PROJ=masakari
CUR_DIR=$(cd "$(dirname "$1")"; pwd)/$(basename "$1")
SRCROOT=$CUR_DIR/../../
PROJ_ROOT=$CUR_DIR/../
RPMBUILD=$SRCROOT/build
SPEC=$CUR_DIR/SPECS/pf9-masakari-controller.spec

PF9_VERSION=${PF9_VERSION:-0.0.7}
BUILD_NUMBER=${BUILD_NUMBER:-0}
PBR_VERSION=1.8.1
export PBR_VERSION
GITHASH=`git rev-parse --short HEAD`

. /opt/rh/python27/enable

# build rpm environment
[ -d $RPMBUILD ] && rm -fr $SRCROOT/rpmbuild
for i in BUILD RPMS SOURCES SPECS SRPMS tmp
do
    mkdir -p $RPMBUILD/${i}
done

cp -f $SPEC $RPMBUILD/SPECS

# build source tarball
tar -cf $RPMBUILD/SOURCES/$PROJ.tar \
    $PROJ_ROOT/controller \
    $PROJ_ROOT/db \
    $PROJ_ROOT/etc \
    $PROJ_ROOT/init.d \
    $PROJ_ROOT/setup.py \
    $PROJ_ROOT/setup.cfg \
    $PROJ_ROOT/requirements.txt \
    $SRCROOT/README.md

# QA_SKIP_BUILD_ROOT is added to skip a check in rpmbuild that greps for
# the buildroot path in the installed binaries. Many of the python
# binary extension .so libraries do this.
QA_SKIP_BUILD_ROOT=1 rpmbuild -ba \
         --define "_topdir $RPMBUILD"  \
         --define "_tmpdir $RPMBUILD/tmp" \
         --define "_version $PF9_VERSION"  \
         --define "_release $BUILD_NUMBER" \
         --define "_githash $GITHASH" \
         $SPEC

${PROJ_ROOT}/sign_packages.sh ${RPMBUILD}/RPMS/*/$PROJ*.rpm
