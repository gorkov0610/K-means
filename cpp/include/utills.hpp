#pragma once
#include <vector>
#include <cmath>

struct point{
    public:
        point(float x, float y, float z) : x(x),y(y),z(z){}
        float x,y,z;

        bool operator==(const point& a) const{
            auto eq = [](float a, float b){
                return std::fabs(a - b) < 1e-6f;
            };
            return eq(x, a.x) && eq(y, a.y) && eq(z, a.z);
        }
};

class cluster{
    public:
        cluster() = default;
        cluster(point& center) : center(center) {}

        point getCenter(){
            return center;
        }

        void calculateCenter(){
            float newX(0), newY(0), newZ(0);
            for(auto i : points){
                newX += i.x;
                newY += i.y;
                newZ += i.z;
            }

            newX /= points.size();
            newY /= points.size();
            newZ /= points.size();

            center.x = newX;
            center.y = newY;
            center.z = newZ;
        }

        void addPoint(point& a){
            points.push_back(a);
        }

        float d(point& a){
            return abs((center.x - a.x) + (center.y - a.y) + (center.z - a.z));
        }

        void clearPoints(){
            points.clear();
        }

        std::vector<point> getPoints(){
            return points;
        }
    private:
        point center;
        std::vector<point> points;
};