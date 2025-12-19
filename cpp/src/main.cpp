#include "../include/json.hpp"
#include "../include/rapidcsv.h"
#include "../include/utills.hpp"
#include <random>
#include <iostream>

using json = nlohmann::ordered_json;
using rapidcsv::Document;
int main(){
    constexpr int numIterations = 100;
    constexpr float eps2 = 1e-8f;

    //parse the json object passed as a runtime argument
    json input;
    
    std::cin >> input;

    //open the dataset specified
    Document dataset(input["dataset"].get<std::string>(),rapidcsv::LabelParams(0, -1), rapidcsv::SeparatorParams(','), rapidcsv::ConverterParams(true));
    
    //declare the clusters and reserve space for them
    int numClusters = input["numClusters"].get<int>();
    std::vector<cluster> clusters;
    clusters.reserve(numClusters);

    //get the data from the points in the dataset
    std::vector<point> instances;
    std::string x = input["fields"][0].get<std::string>();
    std::string y = input["fields"][1].get<std::string>();
    std::string z = input["fields"][2].get<std::string>();
    auto xs = dataset.GetColumn<float>(x);
    auto ys = dataset.GetColumn<float>(y);
    auto zs = dataset.GetColumn<float>(z);
    for(size_t i{0}; i < xs.size(); i++){
        if(std::isnan(xs[i]) || std::isnan(ys[i]) || std::isnan(zs[i])){
            continue;
        }
        instances.emplace_back(xs[i], ys[i], zs[i]);
    }
    
    //get the cluster centroid needed for validation
    int numOfPoints = instances.size();
    float cx{0}, cy{0}, cz{0};
    for(auto& i : instances){
        cx += i.x;
        cy += i.y;
        cz += i.z;
    }
    point datasetCentroid((cx/instances.size()), (cy/instances.size()), (cz/instances.size()));

    if(!input.contains("centers")){
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> distrib(0, numOfPoints - 1);
        for(auto i{0}; i < numClusters; i++){
            clusters.emplace_back(instances[distrib(gen)]);
        }
    }else{
        //get the centers of the clusters and prepare them for clustering
        for(auto& c : input["centers"]){
            point center(c["x"].get<float>(), c["y"].get<float>(), c["z"].get<float>());
            clusters.emplace_back(center);
        }
    }

    int numThreads = std::thread::hardware_concurrency();
    threadPool pool(numThreads);

    //the clustering algorithm
    int iteration{0};
    float eps{1.0};
    size_t chunkSize = static_cast<size_t>(std::ceil(static_cast<float>(instances.size()) / numThreads));
    std::vector<point> oldCenters(numClusters);
    while(iteration < numIterations && eps > eps2){
        for(auto i{0} ; i < numClusters; i++){
            clusters[i].clearPoints();
            oldCenters[i] = clusters[i].getCenter();
        }
        std::vector<std::vector<std::vector<point>>> threadLocalPoints(numThreads, std::vector<std::vector<point>>(numClusters));
        std::vector<std::future<void>> futures;
        for(auto t{0}; t < numThreads; t++){
            auto start = t * chunkSize;
            auto end = std::min(start + chunkSize, instances.size());

            futures.push_back(pool.enqueue([&, t, start, end](){
                for(auto i{start}; i < end; i++){
                    const point& p = instances[i];
                    int best{0};
                    float minD = std::numeric_limits<float>::max();

                    for(auto k{0}; k < numClusters; k++){
                        float dist = clusters[k].d(p);
                        if(dist < minD){
                            minD = dist;
                            best = k;
                        }
                    }
                    threadLocalPoints[t][best].push_back(p);
                }
            }));
        }

        for(auto& f : futures){
            f.get();
        }
        futures.clear();

        for(auto k{0}; k < numClusters; k++){
            for(auto t{0}; t < numThreads; t++){
                for(auto& p : threadLocalPoints[t][k]){
                    clusters[k].addPoint(p);
                }
            }
        }

        for(auto k{0}; k < numClusters; k++){
            futures.push_back(pool.enqueue([&, k](){
                clusters[k].calculateCenter();
            }));
        }
        for(auto& f : futures){
            f.get();
        }
        futures.clear();
        float maxShift{0.0f};
        for(auto i{0}; i < numClusters; i++){
            float shift = (clusters[i].getCenter() - oldCenters[i]).squaredNorm();
            maxShift = std::max(maxShift, shift);
        }

        eps = maxShift;
        iteration++;
    }

    std::vector<std::future<float>> futures;
    float BCSS(0.0);
    for(auto i{0}; i < numClusters; i++){
        float bcss(0.0);
        futures.push_back(pool.enqueue([&clusters, &datasetCentroid, i](){
            return clusters[i].numPoints() * (clusters[i].getCenter() - datasetCentroid).squaredNorm();
        }));
    }
    for(auto& i : futures){
        BCSS += i.get();
    }
    futures.clear();
    float WCSS{0.0};
    for(auto& c : clusters){
        futures.push_back(pool.enqueue([c](){
            float wcss{0.0};
            point clusterCentroid = c.getCenter();
            for(const auto& i : c.getPoints()){
                wcss += (i - clusterCentroid).squaredNorm();
            }
            return wcss;
        }));
    }
    for(auto& i : futures){
        WCSS += i.get();
    }
    float CH = (BCSS / (numClusters - 1)) / (WCSS / (numOfPoints - numClusters));
    json output;
    output["CH_index"] = CH;
    for(auto c{0} ; c < clusters.size(); c++){
        std::string key = "C" + std::to_string(c);
        point center = clusters[c].getCenter();
        output["centers"].push_back({center.x, center.y, center.z});
        std::vector<point> outputCluster = clusters[c].getPoints();
        output[key] = json::array();
        for(auto p:outputCluster){
            output[key].push_back({p.x, p.y, p.z});
        } 
    }
    std::cout << output.dump(2);
    return 0;
}