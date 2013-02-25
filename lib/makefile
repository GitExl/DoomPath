CFLAGS= -Wall -O3 -c

all:

	mkdir -p obj

	gcc $(CFLAGS) -o obj/doompath.o source/doompath.c

	gcc -shared -o doompath.dll obj/*.o $(LIBS)
	strip doompath.dll

	cp doompath.dll ../doompath.dll


clean:

	rm -rf obj
	rm -f doompath.a