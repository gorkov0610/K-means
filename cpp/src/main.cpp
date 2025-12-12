#include "../include/json.hpp"
#include "../include/rapidcsv.h"
#include "../include/utills.hpp"
#include <unordered_map>
#include <iostream>
#include <thread>
#include <future>

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
    
    //get the cluster centroid needed for validation
    int numOfPoints = xs.size();
    float cx(0), cy(0), cz(0);
    for(auto& i : instances){
        cx += i.x;
        cy += i.y;
        cz += i.z;
    }
    point datasetCentroid((cx/instances.size()), (cy/instances.size()), (cz/instances.size()));

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

    threadPool pool(std::thread::hardware_concurrency());

    //the clustering algorithm
    for(auto iteration(0); iteration < maxIterations; iteration++){
        for(auto i(0) ; i < numClusters; i++){
            clusters[i].clearPoints();
        }
        for(const auto& c : instances){
            std::vector<float> distances(numClusters);
            std::vector<std::future<float>> futures;
            for(auto i(0); i < numClusters; i++){
                futures.push_back(pool.enqueue([&k = clusters[i], c](){
                    return k.d(c);
                }));
            }

            for(auto i(0); i < numClusters; i++){
                distances[i] = futures[i].get();
            }
            
            auto it = std::min_element(distances.begin(), distances.end());
            int bestCluster = std::distance(distances.begin(), it);
            clusters[bestCluster].addPoint(c);
        }

        std::vector<std::future<void>> centroidFutures;
        for(auto i(0); i < numClusters; i++){
            centroidFutures.push_back(pool.enqueue([&, i](){
                clusters[i].calculateCenter();
            }));
        }

        for(auto& f : centroidFutures){
            f.get();
        }
    }

    std::vector<std::future<float>> futures;
    float BCSS(0.0);
    for(auto i(0); i < numClusters; i++){
        float bcss(0.0);
        futures.push_back(pool.enqueue([&clusters, &datasetCentroid, i](){
            return clusters[i].numPoints() * (clusters[i].getCenter() - datasetCentroid).squaredNorm();
        }));
    }
    for(auto& i : futures){
        BCSS += i.get();
    }
    futures.clear();
    float WCSS(0.0);
    for(auto& c : clusters){
        futures.push_back(pool.enqueue([c](){
            float wcss(0.0);
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
    for(auto c(0) ; c < clusters.size(); c++){
        std::string key = "C" + std::to_string(c);
        point center = clusters[c].getCenter();
        output["centers"].push_back({center.x, center.y, center.z});
        std::vector<point> outputCluster = clusters[c].getPoints();
        output[key] = json::array();
        for(auto p:outputCluster){
            output[key].push_back({p.x, p.y, p.z});
        } 
    }
    std::cout << output.dump(4);
    return 0;
}