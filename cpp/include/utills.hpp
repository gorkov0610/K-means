#pragma once
#include <vector>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <functional>
#include <atomic>
#include <cmath>
#include <queue>
#include <future>

struct point{
    public:
        point(float x, float y, float z) : x(x),y(y),z(z){}
        float x,y,z;

        float squaredNorm(){
            return x*x + y*y + z*z;
        }
        bool operator==(const point& a) const{
            auto eq = [](float a, float b){
                return std::fabs(a - b) < 1e-6f;
            };
            return eq(x, a.x) && eq(y, a.y) && eq(z, a.z);
        }

        point operator-(const point& a) const{
            return point((x-a.x), (y-a.y), (z-a.z));
        }

};

class cluster{
    public:
        cluster() = default;
        cluster(const point& center) : center(center) {}

        point getCenter() const{
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

        void addPoint(const point& a){
            points.push_back(a);
        }

        float d(const point& a){
            return fabs(center.x - a.x) + fabs(center.y - a.y) + fabs(center.z - a.z);
        }

        void clearPoints(){
            points.clear();
        }

        const std::vector<point>& getPoints() const{
            return points;
        }

        size_t numPoints(){
            return points.size();
        }
    private:
        point center;
        std::vector<point> points;
};

class threadPool{
    public:
        threadPool(uint8_t numThreads) : stop(false){
            for(auto i(0); i < numThreads; i++){
                workers.emplace_back([this](){
                    while (true){
                        std::function<void()> task;
                        {
                            std::unique_lock<std::mutex> lock(this->m);
                            this->cv.wait(lock, [this](){return stop || !tasks.empty();});
                            if(stop && tasks.empty()) return;
                            task = std::move(tasks.front());
                            tasks.pop();
                        }
                        task();
                    }
                });
            }
        }

        template<typename F, typename... Args>
        auto enqueue(F&& f, Args&&... args) -> std::future<decltype(f(args...))>{
            using return_type = decltype(f(args...));

            auto task = std::make_shared<std::packaged_task<return_type()>>(
                std::bind(std::forward<F>(f), std::forward<Args>(args)...)
            );
            std::future<return_type> res = task->get_future();
            {
                std::unique_lock<std::mutex> lock(m);
                tasks.emplace([task](){(*task)();});
            }
            cv.notify_one();
            return res;
        }

        ~threadPool(){
            {
                std::unique_lock<std::mutex> lock(m);
                stop = true;
            }
            cv.notify_all();
            for(std::thread& worker : workers){
                worker.join();
            }
        }
    private:
        std::vector<std::thread> workers;
        std::queue<std::function<void()>> tasks;
        std::mutex m;
        std::condition_variable cv;
        bool stop;
};