#!/usr/bin/python
#
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
#

import sys
import os
import os.path
import re

def get_targets():
    for _, dirs, _  in os.walk('targets'):
        return "#     " + "\n#     ".join(dirs)

PATTERN = re.compile('#include\\s+<\\s*((\w|.)*)\\s*>\\s+')
INCLUDE_DIRS = ['include', 'src']
OBJS_DIR = '_$(TGT)_obs/'

MAKEFILE_HEADER='''
# ############################################################# #
# !! DO NOT EDIT THIS FILE OR INCUDE IT IN _ANY_ GIT COMMITS !! #
# ############################################################# #
# 
# This file was autogenerated using ./genmake.sh You should not have to edit
# this file by hand! If you think you have to edit this file by hand please contact
# the sourceror or look at genmake.sh.
#
# To modify the different attributes of everything, check out the targets
# directory as it contains all the configuration for compilation.
#
# The genmake script will track dependencies and automatically add them to the
# make script. This includes header dependencies.
#
# In this make file, there is a concept of a target (TGT) and environment (ENV)
# The target tells the make file for which architecture we are building
# Currently configured are:
#
''' + get_targets() + '''
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

.INCLUDE_DIRS += targets/$(TGT)/
export ROOT_DIR=.
include targets/$(TGT)/$(ENV).mk 

CXXFLAGS := $(CXXFLAGS) -DTARGET_$(TGT) -DENVIRONMENT_$(ENV)

HACK  := $(shell mkdir -p _$(TGT)_obs/)
HACK2 := $(shell mkdir -p _$(TGT)_obs/tests/)

LDFLAGS := $(LDFLAGS) -lpthread

QEMU?=
export QEMU

default: all
'''

MAKEFILE_FOOTER = '''
clean:
	rm -rf '''+OBJS_DIR+'''
	rm -f mercury

.PHONY: tools tests
tools: notests
	for i in $$(find tools/ -iname "makefile"); do pushd $$(dirname $$i) && make && popd ; done

genmake: genmake.py
	./genmake.py > Makefile


test: tests
	./test.sh

cleanall:
	rm -rf _*_obs
	rm -f mercury

.PHONY: doc
doc:
	doxygen doxygen_config
help:
\t@echo -e "\\nGenmake Makefile help:\\n"
\t@echo -e "   to compile run \`make\`\\n"
\t@echo -e "   There exist several targets and two environments to compile for"
\t@echo -e "   The target to compile for is specified by the environment variable \`TGT\`"
\t@echo -e "   The list of vaild targets is:\\n\\n`ls targets | sed \"s/^/        /g\"`\\n"
\t@echo -e "   In addition to the several targets, there are also two environments:\\n\\n        devel\\n        release\\n"
\t@echo -e "   These are specified by the environment variable \`ENV\`."
\t@echo -e "   In the code, the environment and target being compiled for may be detected by the"
\t@echo -e "   #define ENVIRONMENT_\$$ENV and TARGET_\$$TGT, so #ifdef TARGET_mipsel is true if compiling"
\t@echo -e "   for little endian mips. and ENVIRONMENT_devel is defined when compiling for development.\\n\\n"
\t@echo -e "   How to use this Makefile:\\n\\n"
\t@echo -e "       all:      make everything except documentation (this is default)"
\t@echo -e "       notests:  make the binary, but not the testing binaries"
\t@echo -e "       test:     build and run all tests"
\t@echo -e "       doc:      build the documentation for the codebase"
\t@echo -e "       clean:    clean for the current target"
\t@echo -e "       cleanall: clean for all targets"
\t@echo -e "       genmake:  run genmake.sh (do this after adding a new cpp file)\\n"
\t@echo -e "   Tips:\\n"
\t@echo -e "       - The makefile targets/\$$TGT/\$$ENV.mk is included. This is how the different environments are achieved.\\n"
\t@echo -e "       - Tests for the codebase are stored in the tests/ directory. Tests with an underscore \`_\` in front are disabled by default.\\n"
\t@echo -e "       - Everytime you add a new source file, you must regenerate the makefile with make genmake (or ./genmake.sh > Makefile).\\n"
\t@echo -e "       - Object files and binaries are stored in _\$$TGT_obs\\n"
\t@echo -e "       - Source is stored in the src directory and header files are stored in the include directory.\\n\\n"
\t@echo -e "       For _even_ more information, read the comment at the top of Makefile"
'''

def get_dependencies(f):
    sys.stderr.write('    Trace ' + f + '\n')
    ret = set()
    fd = open(f, 'r')
    for line in fd.readlines():
        match = PATTERN.match(line)
        if match:
            newdep = dependency_to_full_path(match.group(1))
            if newdep != None:
                ret.add(newdep)
                ret.update(get_dependencies(newdep))
    return ret

# Return all the cpp source files
def get_source_files():
    for dirpath, dirs, files in os.walk('.'):
        for i in files:
            f = os.path.join(dirpath, i)
            if f.endswith('.cpp') and not f.startswith('main'):
                sys.stderr.write('Source: ' + f + '\n')
                yield (f, get_dependencies(f))


def to_object_file(f):
    if f.startswith('./'):
        f = f[2:]

    return OBJS_DIR + f.replace('.cpp', '.o').replace('/', '_')

def dependency_to_full_path(dep):
    for incl in INCLUDE_DIRS:
        rincl = incl + '/' + dep
        if os.path.isfile(rincl):
            return rincl
    return None

def prelude():
    sys.stdout.write(MAKEFILE_HEADER)

def main(argv):
    prelude()

    source_files = [i for i in get_source_files()]
    object_files = [to_object_file(i[0]) for i in source_files]
    zipped = list(zip(source_files, object_files))
    test_binaries = []

    for ((source_file, dependencies), object_file) in zipped:
        if source_file.startswith('./tests/'):
            binary = object_file[:-2]
            test_binaries.append(binary)
            sys.stdout.write(binary + ': ' + OBJS_DIR + 'libmercury.a ' + object_file + '\n')
            sys.stdout.write('\t$(CXX) -o ' + binary + ' ' + object_file + ' ' + OBJS_DIR + 'libmercury.a $(LDFLAGS)\n\n')

    for ((source_file, dependencies), object_file) in zipped:
        sys.stdout.write(object_file + ': ' + source_file + ' ' + '\\\n    '.join(dependencies) + '\n')
        sys.stdout.write('\t$(CXX) $(CXXFLAGS) -c -o %s %s\n\n' % (object_file, source_file))

    sys.stdout.write(OBJS_DIR + 'libmercury.a: ' + '\\\n    '.join(object_files) + '\n')
    sys.stdout.write('\t$(AR) -rcs '+OBJS_DIR+'/libmercury.a ' + '\\\n    '.join(object_files) + '\n\n')

    sys.stdout.write('notests:' + ' main.cpp '+OBJS_DIR+'libmercury.a\n')
    sys.stdout.write('\t$(CXX) -o main '+OBJS_DIR+'libmercury.a $(LDFLAGS)\n\n')

    sys.stdout.write('tests: ' + '\\\n    '.join(test_binaries))
    sys.stdout.write('\n\n')

    sys.stdout.write('all: tests notests tools')
    sys.stdout.write('\n\n')

    sys.stdout.write(MAKEFILE_FOOTER)

if __name__ == "__main__":
    main(sys.argv)
