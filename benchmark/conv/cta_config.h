#ifndef NUM_BLOCKS 
#define NUM_BLOCKS 512
#endif 


#ifndef NUM_THREADS_X  
#define NUM_THREADS_X 32
#endif


#ifndef NUM_THREADS_Y 
#define NUM_THREADS_Y 4
#endif 


#ifndef BLOCK_SIZE 
#define BLOCK_SIZE 32
#endif 


#ifndef CLAMP
#define CLAMP(x, a, b) { \
    if (x < (a)) {x = (a);} \
    if (x >= (b)) {x = ((b) - 1);} \
}
#endif 
