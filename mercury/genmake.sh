#!/bin/bash

# This script will recursively locate c++ files and try to extract
# their dependencies to create a robust and automatically generated
# Makefile that has extensibility features built in.
#
# To use this script to genrate a makefile, make sure to be in the directory
# of the project (oplabs.git/mercury) and run the command:
#
#   $ ./genmake.sh > Makefile
#
# To learn how to use the makefile, generate it and read the comments
# at the top (or look down like 4 inches)

function discover_depends {
    local depth=$2
    if [ -z $depth ] ; then 
        depth=1
    fi

    if [[ $depth -gt 20 ]] ; then
        echo "Max dependency depth exceeded" >&2
    else
	    file=$1
	    includes=$(cat $file | perl -ne '/#include\s*<(.*)>/ && print "$1\n"')
	    
	    for i in $includes ; do
	        if [[ -e "include/$i" ]] ; then
	            echo -n -e ' \\\n         include/'$i
	            discover_depends "include/$i" $(($depth + 1))
	        fi
	    done 
    fi
}


source_files=$(find * -name '*cpp' -and -not -name 'main.cpp' -and -not -name 'test_*')
mains=$(find * -name 'main_*.cpp')

cat <<- EOF
# This file was autogenerated using ./genmake.sh You should not have to edit
# this file by hand!  If you do have to edit this file by hand please contact
# the sourceror
#
# To modify the different attributes of everything, check out the targets
# directory as it contains all the configuration for compilation.
#
# The genmake script will track dependencies and automatically add them to the
# make script. This includes header dependencies.
#
# In this make file, there is a concept of a target (TGT) and environment (ENV)
# The target tells the make file for which architecture we are building
# Currently only two are configured: x86 and i386.
#
# The environment specifies what environment we are using (e.g. devel, test, release)
#
# What these variables actually specify is a .mk file for this make file to include
# according to the template:
#
#           targets/TGT/ENV.mk
#
# examples of how to use this Makefile:
#   
#   $ make                      # builds x86 development binary (default)
#   $ TGT=x86 ENV=devel make    # explcitly builds x86 development binary (default)
#   $ TGT=i386 ENV=release make # builds release i386
#   $ TGT=i386 make             # builds devel i386
#   $ ENV=devel make            # builds devel x86
#   $ ENV=flyingspaghettimonster make            # builds flyingspaghettimonster x86 (if such a thing exists)
#

SHELL=/bin/bash

TGT?=x86_64
ENV?=devel

.INCLUDE_DIRS += targets/\$(TGT)/
include targets/\$(TGT)/\$(ENV).mk 

CXXFLAGS := \$(CXXFLAGS) -DTARGET_\$(TGT)

HACK  := \$(shell mkdir -p _\$(TGT)_obs/)
HACK2 := \$(shell mkdir -p _\$(TGT)_obs/tests/)

LDFLAGS := \$(LDFLAGS) -lpthread

QEMU?=
export QEMU

default: all
EOF

OBS_DIR='_$(TGT)_obs'
LIBRARY="$OBS_DIR/libmerc.a"


objects=""

for file in $source_files ; do
    obj_file=${file/cpp/o}
    obj_file=$OBS_DIR/${obj_file//\//_}

    echo "$obj_file: $file $(discover_depends $file)"
    echo '	$(CXX) -o '$obj_file' $(CXXFLAGS) -c '$file
    echo ''

    objects=$objects' '$obj_file
done

test_sources=$(find tests/ -name '*.cpp')
test_binaries=""
for test_src in $test_sources ; do
    obj_file=${test_src/cpp/o}
    obj_file=$OBS_DIR/${obj_file//\//_}

    binary=${test_src/.cpp/}
    binary=$OBS_DIR/$binary

    test_binaries="$test_binaries $binary"

    echo "$binary: $obj_file $LIBRARY"
    echo '	$(CXX) -o '$binary' $(CXXFLAGS) '$obj_file' '$LIBRARY '$(LDFLAGS)'
    echo ''
done


echo 'clean:'
echo '	rm -rf '$OBS_DIR'/'
echo '	rm -f mercury'
echo ''
echo ''$OBS_DIR'/libmerc.a: '$objects
echo '	$(AR) -r $@ $^'
echo ''
echo 'all:' $LIBRARY "$(discover_depends main.cpp | awk ' !x[$0]++') tests"
echo '	$(CXX) -o '$OBS_DIR'/mercury main.cpp $(CXXFLAGS) -L '$OBS_DIR'/ -lmerc' '$(LDFLAGS)'
echo '	ln -sf '$OBS_DIR'/mercury .'
echo ''
echo 'genmake: genmake.sh'
echo '	./genmake.sh > Makefile'
echo ''
echo 'tests: '$test_binaries
echo ''
# echo 'tests: _$(TGT)_obs/libmerc.a'
# echo '	mkdir -p _$(TGT)_obs/tests/'
# echo '	for i in $$(ls tests/*.cpp) ; do \'
# echo '		out=_$(TGT)_obs/$${i/%.cpp/} ; \'
# echo '		if [ "$$i" -nt "$$out" ] ; then \'
# echo '			echo g++ $$i -o $$out _$(TGT)_obs/libmerc.a ; \'
# echo '			g++ $(CXXFLAGS) $$i -o $$out _$(TGT)_obs/libmerc.a ; \'
# echo '		fi ; \'
# echo '	done'
echo ''
echo 'test: tests'
echo '	./test.sh'
echo ''
echo 'cleanall:'
echo '	rm -rf _*_obs'
echo '	rm -f mercury'

