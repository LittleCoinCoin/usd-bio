#include <iostream>
#include <usd_bio/extension.h>

int main() {
    std::cout << "USD-Bio Extension v" 
              << usd_bio::GetVersion() 
              << std::endl;
    return 0;
}
