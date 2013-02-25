#include "doompath.h"


#define NODE_FLAG_SUBSECTOR    0x8000

#define SECTOR_SIZE 26
#define SUBSECTOR_SIZE 4
#define SEG_SIZE 12
#define NODE_SIZE 28
#define VERTEX_SIZE 4
#define SIDEDEF_SIZE 30
#define LINEDEF_SIZE 14


typedef struct {
    int16_t floorheight;
    int16_t ceilingheight;
    char floorpic[8];
    char ceilingpic[8];
    int16_t lightlevel;
    int16_t special;
    int16_t tag;
} sector_t;

typedef struct {
    int16_t num_segs;
    int16_t first_seg;
} subsector_t;

typedef struct {
    int16_t vertex1;
    int16_t vertex2;
    int16_t angle;
    int16_t linedef;
    int16_t side;
    int16_t offset;
} seg_t;

typedef struct {
    int16_t x;
    int16_t y;
    int16_t delta_x;
    int16_t delta_y;
    int16_t bbox[2][4];
    uint16_t children[2];
} node_t;

typedef struct {
    int16_t x;
    int16_t y;
} vertex_t;

typedef struct {
    int16_t offset_x;
    int16_t offset_y;
    char texture_top[8];
    char texture_bottom[8];
    char texture_mid[8];
    int16_t sector;
} sidedef_t;

typedef struct {
    int16_t vertex1;
    int16_t vertex2;
    int16_t flags;
    int16_t special;
    int16_t tag;
    int16_t sidedefs[2];
} linedef_t;

typedef struct {
    uint32_t num_vertices;
    vertex_t *vertices;

    uint32_t num_segs;
    seg_t    *segs;

    uint32_t num_sectors;
    sector_t *sectors;

    uint32_t num_subsectors;
    subsector_t *subsectors;

    uint32_t num_nodes;
    node_t   *nodes;

    uint32_t num_lines;
    linedef_t   *lines;

    uint32_t num_sides;
    sidedef_t   *sides;
} mapdata_t;


mapdata_t* mapdata_create() {
    mapdata_t* mapdata = calloc(1, sizeof(mapdata_t));
    return mapdata;
}

void mapdata_free(mapdata_t* mapdata) {
    free(mapdata);
}

void mapdata_put_vertices(mapdata_t* mapdata, uint32_t num_vertices, void* vertex_data) {
    uint32_t i = 0;

    mapdata->num_vertices = num_vertices;
    
    mapdata->vertices = calloc(1, sizeof(vertex_t) * num_vertices);
    for (i = 0; i < num_vertices; i++) {
        memcpy(mapdata->vertices + i, vertex_data + i * VERTEX_SIZE, VERTEX_SIZE);

    }
}

void mapdata_put_nodes(mapdata_t* mapdata, uint32_t num_nodes, void* node_data) {
    uint32_t i = 0;

    mapdata->num_nodes = num_nodes;
    
    mapdata->nodes = calloc(1, sizeof(node_t) * num_nodes);
    for (i = 0; i < num_nodes; i++) {
        memcpy(mapdata->nodes + i, node_data + i * NODE_SIZE, NODE_SIZE);
     }
}


uint16_t point_on_node_side(mapdata_t* mapdata, int16_t x, int16_t y, node_t* node) {
    if (node->delta_x == 0) {
        if (x <= node->x) {
            return (node->delta_y > 0);
        } else {
            return (node->delta_y < 0);
        }
        
    } else if (node->delta_y == 0) {
        if (y <= node->y) {
            return (node->delta_x < 0);
        } else {
            return (node->delta_x > 0);
        }
    }

    x -= node->x;
    y -= node->y;

    if ((node->delta_y ^ node->delta_x ^ x ^ y) < 0) {
        return (node->delta_y ^ x) < 0;
    }
    
    return y * node->delta_x >= node->delta_y * x;
}

uint16_t point_in_subsector(mapdata_t* mapdata, const int16_t x, const int16_t y) {
    uint16_t node_index = mapdata->num_nodes - 1;

    while ((node_index & NODE_FLAG_SUBSECTOR) == 0) {
        node_index = mapdata->nodes[node_index].children[point_on_node_side(mapdata, x, y, &mapdata->nodes[node_index])];
    }

    return node_index & ~NODE_FLAG_SUBSECTOR;
}


int8_t box_intersects_line(const int32_t x1, const int32_t y1, const int32_t x2, const int32_t y2, const int32_t left, const int32_t top, const int32_t right, const int32_t bottom) {

    if (x1 < left && x2 >= left) {
        int32_t iy = y1 + (y2 - y1) * (left - x1) / (x2 - x1);
        if (iy >= bottom && iy <= top) {
            return 1;
        }
    } else if (x1 > right && x2 <= right) {
        int32_t iy = y1 + (y2 - y1) * (right - x1) / (x2 - x1);
        if (iy >= bottom && iy <= top) {
            return 1;
        }
    }

    if (y1 < bottom && y2 >= bottom) {
        int32_t ix = x1 + (x2 - x1) * (bottom - y1) / (y2 - y1);
        if (ix >= left && ix <= right) {
            return 1;
        }
    } else if (y1 > top && y2 <= top) {
        int32_t ix = x1 + (x2 - x1) * (top - y1) / (y2 - y1);
        if (ix >= left && ix <= right) {
            return 1;
        }
    }

    return 0;
}


#define SLOPE_HORIZONTAL 1
#define SLOPE_VERTICAL 2
#define SLOPE_POSITIVE 3
#define SLOPE_NEGATIVE 4

uint16_t point_on_line_side(const int16_t x, const int16_t y, const int16_t x1, const int16_t y1, const int16_t x2, const int16_t y2, const int16_t dx, const int16_t dy) {
    if (!dx) {
        return (x <= x1) ? (dy > 0) : (dy < 0);
    } else if (!dy) {
        return (y <= y1) ? (dx < 0) : (dx > 0);
    } else {
        return (dy * x - x1) <= (y - y1 * dx);
    }
}

int8_t box_on_line_side(const int16_t left, const int16_t top, const int16_t right, const int16_t bottom, const int16_t x1, const int16_t y1, const int16_t x2, const int16_t y2) {
    int16_t p1 = 0;
    int16_t p2 = 0;
    uint8_t slopetype = 0;

    int16_t dx = x2 - x1;
    int16_t dy = y2 - y1;
    
    if (!dx) {
        slopetype = SLOPE_VERTICAL;
    } else if (!dy) {
        slopetype = SLOPE_HORIZONTAL;
    } else {
        if ((double)(dy / dx) > 0) {
            slopetype = SLOPE_POSITIVE;
        } else {
            slopetype = SLOPE_NEGATIVE;
        }
    }

    switch (slopetype) {
        case SLOPE_HORIZONTAL:
            p1 = top > y1;
            p2 = bottom > y1;
            if (dx < 0) {
                p1 ^= 1;
                p2 ^= 1;
            }
            break;

        case SLOPE_VERTICAL:
            p1 = right < x1;
            p2 = left < x1;
            if (dy < 0) {
                p1 ^= 1;
                p2 ^= 1;
            }
            break;

        case SLOPE_POSITIVE:
            p1 = point_on_line_side(left, top, x1, y1, x2, y2, dx, dy);
            p2 = point_on_line_side(right, bottom, x1, y1, x2, y2, dx, dy);
            break;

        case SLOPE_NEGATIVE:
            p1 = point_on_line_side(right, top, x1, y1, x2, y2, dx, dy);
            p2 = point_on_line_side(left, bottom, x1, y1, x2, y2, dx, dy);
            break;
    }

    return (p1 == p2) ? p1 : -1;
}