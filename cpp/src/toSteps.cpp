#include <iostream>
#include <json/value.h>
#include <json/json.h>
#include <algorithm>
#include <fstream>
#include <variant>
#include <vector>
#include <sstream>
#include <string>
#include <cmath>

using ImgElement = std::variant<std::string, std::pair<double, double>>;

int convertToSteps(std::string settings_json, std::string _input_file,std::string _output_file, bool fit, bool min_pen_pickup);
int remap(int x, int in_min, int in_max, int out_min, int out_max);
std::vector<int> calculate(double vector[2], const int& s_distance_between_motors, int (&s_current_distance)[2]);

int main() {
    convertToSteps(
                    R"(C:\Users\tvten\Programming\DrawingMachine\settings.json)", 
                    R"(C:\Users\tvten\Programming\DrawingMachine\generated_files\output_coordinates.txt)", 
                    R"(C:\Users\tvten\Programming\DrawingMachine\generated_files\path_cpp.txt)", 
                    true, 
                    false);

    return 0;

    /*
    std::fstream file;
    file.open("test.txt", std::ios::in);

    if (file.is_open()) {
        std::string line;
        while (std::getline(file, line)) {
            std::cout << line << std::endl;
        }
        file.close();
    }

    file.open("test.txt", std::ios::out);

    if (file.is_open()) {
        file << "test\n";
        file.close();
    }

    file.open("test.txt", std::ios::app);

    if (file.is_open()) {
        file << "test22";
        file.close();
    }

    return 0;*/
}

int convertToSteps(std::string settings_json, std::string _input_file, std::string _output_file, bool fit, bool min_pen_pickup) {
    int tooth_on_gear;
    int steps_per_rev;
    int motor_dir[2];
    int mm_belt_tooth_distance;
    int mm_distance_between_motors;
    int mm_start_distance[2];
    int mm_paper_dimensions[2];
    int mm_paper_offset_from_start;


    std::ifstream file(settings_json);
    Json::Value jsonValue;
    Json::Reader jsonReader;

    std::cout << "Parsing JSON" << std::endl;

    jsonReader.parse(file, jsonValue);
    tooth_on_gear = jsonValue["toothOngear"].asInt();
    steps_per_rev = jsonValue["stepsPerRev"].asInt();
    motor_dir[0] = jsonValue["motorDir"][0].asInt();
    motor_dir[1] = jsonValue["motorDir"][1].asInt();
    mm_belt_tooth_distance = jsonValue["beltToothDistance"].asInt();
    mm_distance_between_motors = jsonValue["distanceBetweenMotors"].asInt();
    mm_start_distance[0] = jsonValue["startDistance"][0].asInt();
    mm_start_distance[1] = jsonValue["startDistance"][1].asInt();
    mm_paper_dimensions[0] = jsonValue["paperSize"][0].asInt();
    mm_paper_dimensions[1] = jsonValue["paperSize"][1].asInt();
    mm_paper_offset_from_start = jsonValue["paperOffset"].asInt();

    /*
    std::cout << "toothOngear: " << tooth_on_gear << std::endl;
    std::cout << "stepsPerRev: " << steps_per_rev << std::endl;
    std::cout << "motorDir: " << motor_dir[0] << ", " << motor_dir[1] << std::endl;
    std::cout << "beltToothDistance: " << mm_belt_tooth_distance << std::endl;
    std::cout << "distanceBetweenMotors: " << mm_distance_between_motors << std::endl;
    std::cout << "startDistance: " << mm_start_distance[0] << ", " << mm_start_distance[1] << std::endl;
    std::cout << "paperSize: " << mm_paper_dimensions[0] << ", " << mm_paper_dimensions[1] << std::endl;
    std::cout << "paperOffset: " << mm_paper_offset_from_start << std::endl;
    */

    std::cout << "Converting mms to steps" << std::endl;

    double mm_per_step = mm_belt_tooth_distance * tooth_on_gear / (double)steps_per_rev;
    int s_distance_between_motors = mm_distance_between_motors / mm_per_step;
    int s_start_distance[2] = {(int)(mm_start_distance[0] / mm_per_step), (int)(mm_start_distance[1] / mm_per_step)};
    int s_paper_dimensions[2] = {(int)(mm_paper_dimensions[0] / mm_per_step), (int)(mm_paper_dimensions[1] / mm_per_step)};
    int s_paper_offset_from_start = (int)(mm_paper_offset_from_start / mm_per_step);
    int s_paper_offset_calculated[2] = {
        (((s_distance_between_motors / 2) - (s_paper_dimensions[0] / 2))),
        ((int)sqrt(pow(s_start_distance[0], 2) - pow((s_distance_between_motors / 2), 2)) - s_paper_offset_from_start - s_paper_dimensions[1])};
        
    int s_current_distance[2];
    std::copy(std::begin(s_start_distance), std::end(s_start_distance), std::begin(s_current_distance));


    std::cout << "Reading input file" << std::endl;

    std::fstream input_file;
    input_file.open(_input_file, std::ios::in);

    std::vector<ImgElement> imgs;
    double max_x = 0;
    double max_y = 0;

    if (!input_file.is_open()) {
        std::cerr << "Error opening file: " << _input_file << std::endl;
        return -1;
    }
    
    std::string line;
    while (std::getline(input_file, line)) {
        line = std::string(line.begin(), remove(line.begin(), line.end(), '\r'));

        if (line == "PAUSE" || line == "PENUP" || line == "PENDOWN") {
            imgs.push_back(line);
        } 
        else {
            std::stringstream ss(line);
            std::vector<std::string> split_string;
            std::vector<double> split_double;
            while (std::getline(ss, line, ' ')) {
                split_string.push_back(line);
            }
            split_double.push_back(std::stod(split_string[0]));
            split_double.push_back(std::stod(split_string[1]));

            if (split_double[0] > max_x) {
                max_x = split_double[0];
            }
            if (split_double[1] > max_y) {
                max_y = split_double[1];
            }
        }
    }

    input_file.close();


    std::cout << "Max X: " << max_x << std::endl;
    std::cout << "Max Y: " << max_y << std::endl;
    
    //[33569, 33979.981132075474]
    //[5835, 14556]

    double test[2] = {33569, 33979.981132075474};

    std::vector<int> s_change = calculate(test, s_distance_between_motors, s_current_distance);

    std::cout << s_change[0] << " " << s_change[1];

    //[5835, 14556]


    return 0;
}

int remap(int x, int in_min, int in_max, int out_min, int out_max) {
    return (int)((x - in_min) * (out_max - out_min) / (double)(in_max - in_min) + out_min);
}

std::vector<int> calculate(double vector[2], const int& s_distance_between_motors, std::vector<int>& s_current_distance) {
    std::vector<int> s_new_distance = {
        static_cast<int>(sqrt(pow(vector[0], 2) + pow(vector[1], 2))),
        static_cast<int>(sqrt(pow((s_distance_between_motors - vector[0]), 2) + pow(vector[1], 2)))
    };

    std::vector<int> s_change = {
        (s_current_distance[0] - s_new_distance[0]),
        (s_current_distance[1] - s_new_distance[1])
    };

    s_current_distance[0] = round(s_new_distance[0]);
    s_current_distance[1] = round(s_new_distance[1]);

    return s_change;
}