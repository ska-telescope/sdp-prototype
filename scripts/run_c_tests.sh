#!/bin/bash

bold=$(tput bold)
normal=$(tput sgr0)

#temp hack
cd app

cd src/vis_receive
[[ -e ./build ]] && printf "\n**** removing old build directory ****\n" && rm -rf ./build
echo -e "\n ${bold}*** Running Cpp Check *** ${normal} \n"
cppcheck ./ -i extern/gtest/ --enable=warning,portability,style
mkdir ./build
cd ./build

echo -e "\n ${bold}*** Running Undefined Behaviour Sanitizer *** ${normal} \n"
#cd .. && rm -r -f build && mkdir build && cd build
rm -rf *
cmake -DENABLE_USAN=ON ..
make
./tests/recv_test

echo -e "\n ${bold}*** Running Threading Sanitizer *** ${normal} \n"
#cd .. && rm -r -f build && mkdir build && cd build
rm -rf *
cmake -DENABLE_TSAN=ON ..
make
./tests/recv_test

echo -e "\n ${bold}*** Running Address Sanitizer *** ${normal} \n"
#cd .. && rm -r -f build && mkdir build && cd build
rm -rf *
cmake -DENABLE_ASAN=ON ..
make
./tests/recv_test

rm -rf *
cmake -DCOVERALLS=ON -DCMAKE_BUILD_TYPE=Debug ..

echo -e "\n ${bold}*** Running Coveralls *** ${normal} \n"
if cmake -DCOVERALLS=ON -DCMAKE_BUILD_TYPE=Debug ..
then
   make
   make coveralls

   # echo -e "\n ${bold}*** Running Valgrind using Ctest testing tool *** ${normal} \n"
   # ctest -T memcheck
else
   echo -e "\n ${bold}*** Unable to run Coveralls or Valgrind *** ${normal} \n"
fi
