#include "../include/json.hpp"
#include "../include/rapidcsv.h"
#include "../include/utills.hpp"
#include <unordered_map>
#include <iostream>
#include <thread>

using json = nlohmann::ordered_json;
using rapidcsv::Document;
int main(){
    //parse the json object passed as a runtime argument
    json input;
    
    std::cin >> input;

    //open the dataset specified
    Document dataset(input["dataset"].get<std::string>());
    
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
    for(size_t i(0); i < xs.size(); i++){
        instances.emplace_back(xs[i], ys[i], zs[i]);
    }

    //get the centers of the clusters and prepare them for clustering
    for(auto& c : input["centers"]){
        point center(c["x"].get<float>(), c["y"].get<float>(), c["z"].get<float>());
        clusters.emplace_back(center);
        instances.erase(
            std::remove(instances.begin(), instances.end(), center),
            instances.end()
        );
    }

    //read the maximum iterations
    int maxIterations = input["iterations"].get<int>();

    //the clustering algorithm
    for(auto iteration(0); iteration < maxIterations; iteration++){
        for(auto i(0) ; i < numClusters; i++){
            clusters[i].clearPoints();
        }
        for(auto c : instances){
            std::vector<uint32_t> distances;
            distances.resize(numClusters);
            std::vector<std::thread> distanceCalculatingThreads;
            for(auto i(0); i < numClusters; i++){
                distanceCalculatingThreads.emplace_back([&, i](){
                    distances[i] = clusters[i].d(c);
                });
            }
            for(auto& t : distanceCalculatingThreads){
                t.join();
            }

            auto it = std::min_element(distances.begin(), distances.end());
            int bestCluster = std::distance(distances.begin(), it);
            clusters[bestCluster].addPoint(c);
        }
        std::vector<std::thread> centroidThreads;
        for(auto i(0); i < numClusters; i++){
            centroidThreads.emplace_back([&, i](){
                clusters[i].calculateCenter();
            });
        }
        for(auto& t : centroidThreads){
            t.join();
        }
    }

    json output;
    for(auto c(0) ; c < clusters.size(); c++){
        std::string key = "C" + std::to_string(c);
        point center = clusters[c].getCenter();
        output["centers"].push_back({center.x, center.y, center.z});
        std::vector<point> outputCluster = clusters[c].getPoints();
        for(auto p:outputCluster){
            output[key].push_back({p.x, p.y, p.z});
        } 
    }
    std::cout << output.dump();
    return 0;
}