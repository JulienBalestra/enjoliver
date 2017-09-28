#!/bin/bash -e

DIR=$PWD/work
mkdir -p ${DIR}
rm -f ${DIR}/*.tar.gz


LIBRESSL=libressl-2.4.5
HAPROXY=haproxy-1.7.5
PCRE=pcre-8.39
LUA=lua-5.3.0
READLINE=readline-6.3
NCURSES=ncurses-6.0
ZLIB=zlib-1.2.11

cd ${DIR}
rm -rf ${NCURSES}
export STATIC_NCURSES=${DIR}/target/${NCURSES}
wget https://ftp.gnu.org/pub/gnu/ncurses/${NCURSES}.tar.gz
tar xvzf ${NCURSES}.tar.gz
cd ${NCURSES}
./configure --prefix=${STATIC_NCURSES} --enable-shared=no
make && make install
export LD_LIBRARY_PATH=${STATIC_NCURSES}/lib:${LD_LIBRARY_PATH}

cd ${DIR}
rm -rf ${ZLIB}
export STATIC_ZLIB=${DIR}/target/${ZLIB}
wget http://zlib.net/${ZLIB}.tar.gz
tar xvzf ${ZLIB}.tar.gz
cd ${ZLIB}
./configure --prefix=${STATIC_ZLIB} --static
make && make install
export LD_LIBRARY_PATH=${STATIC_ZLIB}/lib:${LD_LIBRARY_PATH}


cd ${DIR}
rm -rf ${READLINE}
export STATIC_READLINE=${DIR}/target/${READLINE}
wget https://ftp.gnu.org/gnu/readline/${READLINE}.tar.gz
tar xvzf ${READLINE}.tar.gz
cd ${READLINE}
./configure --prefix=${STATIC_READLINE} --enable-static=true
make && make install
export LD_LIBRARY_PATH=${STATIC_READLINE}/lib:${LD_LIBRARY_PATH}

cd ${DIR}
rm -rf ${LUA}
wget http://www.lua.org/ftp/${LUA}.tar.gz
export STATIC_LUA=${DIR}/target/${LUA}
tar xvzf ${LUA}.tar.gz
cd ${LUA}
make MYCFLAGS="-I${STATIC_READLINE}/include" MYLDFLAGS="-L${STATIC_READLINE}/lib -L${STATIC_NCURSES}/lib -lreadline -lncurses"  linux
make INSTALL_TOP=${DIR}/target/${LUA}  install
export LD_LIBRARY_PATH=${STATIC_LUA}/lib:${LD_LIBRARY_PATH}

cd ${DIR}
wget http://ftp.openbsd.org/pub/OpenBSD/LibreSSL/${LIBRESSL}.tar.gz
export STATIC_LIBRESSL=${DIR}/target/${LIBRESSL}
tar xvzf ${LIBRESSL}.tar.gz
cd ${LIBRESSL}
./configure  --prefix=$STATIC_LIBRESSL --enable-shared=no
make && make install
cd ${DIR}

export STATIC_PCRE=${DIR}/target/${PCRE}
wget ftp://ftp.csx.cam.ac.uk/pub/software/programming/pcre/${PCRE}.tar.gz

tar xvzf ${PCRE}.tar.gz
cd  ${PCRE}
./configure --prefix=$STATIC_PCRE --enable-shared=no --enable-utf8 --enable-jit
make && make install

cd ${DIR}

wget http://www.haproxy.org/download/1.7/src/${HAPROXY}.tar.gz

tar xvzf ${HAPROXY}.tar.gz
cd ${HAPROXY}
make TARGET=linux2628 USE_PCRE_JIT=1 USE_LUA=1 USE_ZLIB=1 USE_STATIC_PCRE=1 USE_OPENSSL=1 ZLIB_LIB=${STATIC_ZLIB}/lib ZLIB_INC=${STATIC_ZLIB}/include PCRE_LIB=${STATIC_PCRE}/lib PCRE_INC=${STATIC_PCRE}/include  SSL_INC=${STATIC_LIBRESSL}/include SSL_LIB=${STATIC_LIBRESSL}/lib LUA_INC=${STATIC_LUA}/include LUA_LIB=${STATIC_LUA}/lib ADDLIB="-ldl -lrt -lz"
make  DESTDIR=${DIR}/target/haproxy/ install

cd ${DIR}