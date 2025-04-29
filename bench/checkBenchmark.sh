#!/bin/bash

#COMPILER=gcc # Please adapt this line to your favorite compiler.
COMPILER=patmos-clang

OPTIONS=" -O2 "

#EXEC= # Adapt if the executable is to be executed via another program
#EXEC=valgrind\ -q
EXEC=~/t-crest/simulator/build/src/pasim

PASS=0
FAIL_COMP=0
FAIL_EXEC=0

# Check if exec_option is provided as a command-line argument
if [ $# -lt 1 ]; then
    echo "Usage: $0 <exec_option>"
    exit 1
fi
exec_option="${@:2}"
# Extract the bench tag from the first argument
bench_tag="$1"


for dir in */; do

    cd "$dir"

    printf "Entering ${dir} \n"

    for BENCH in */; do
        cd "$BENCH"
                
        # Remove trailing slash from BENCH
        BENCH_NAME=$(basename "$BENCH")
        
        # Append the exec_prefix to BENCH_NAME
        BENCH_NAME="${BENCH_NAME}_${bench_tag}"

        printf "Checking ${BENCH_NAME} ..."
        if [ -f a.out ]; then
            rm a.out
        fi
        
        if [ -f *.o ]; then
            rm *.o
        fi
        
        
        # Please remove '&>/dev/null' to identify the warnings (if any)
        $COMPILER $OPTIONS *.c
        
        if [ -f a.out ]; then
            rm -f "$BENCH_NAME.pasim"
            touch "$BENCH_NAME.pasim"
            $EXEC $exec_option ./a.out 2> "$BENCH_NAME.pasim"
            RETURNVALUE=$(echo $?)
            if [ $RETURNVALUE -eq 0 ]; then
                printf "passed. \n"
                ((PASS++))
            else
                printf "failed (wrong return value $RETURNVALUE). \n"
                ((FAIL_EXEC++))
            fi
        else
            printf "failed (compiled with errors/warnings). \n"
            ((FAIL_COMP++))
        fi 
        
        cd ..
    done

    printf "Leaving ${dir} \n\n"
    
    cd ..
done

echo "PASS: $PASS, FAIL_COMP: $FAIL_COMP, FAIL_EXEC: $FAIL_EXEC"