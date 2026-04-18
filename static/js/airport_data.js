// Airport data by country/city for dropdown selection
const AIRPORT_DATA = {
    // India
    "india": [
        { code: "DEL", name: "Indira Gandhi Intl", city: "New Delhi" },
        { code: "BOM", name: "Chhatrapati Shivaji Intl", city: "Mumbai" },
        { code: "BLR", name: "Kempegowda Intl", city: "Bangalore" },
        { code: "HYD", name: "Rajiv Gandhi Intl", city: "Hyderabad" },
        { code: "MAA", name: "Chennai Intl", city: "Chennai" },
        { code: "CCU", name: "Netaji Subhash Intl", city: "Kolkata" },
        { code: "COK", name: "Cochin Intl", city: "Kochi" },
        { code: "PNQ", name: "Pune Intl", city: "Pune" },
        { code: "AMD", name: "Sardar Vallabhbhai Patel Intl", city: "Ahmedabad" },
        { code: "GOI", name: "Goa Intl (Dabolim)", city: "Goa" },
    ],
    // USA — individual cities
    "atlanta": [
        { code: "ATL", name: "Hartsfield-Jackson Atlanta Intl", city: "Atlanta" },
    ],
    "mobile": [
        { code: "MOB", name: "Mobile Regional Airport", city: "Mobile" },
    ],
    "new york": [
        { code: "JFK", name: "John F. Kennedy Intl", city: "New York" },
        { code: "LGA", name: "LaGuardia Airport", city: "New York" },
        { code: "EWR", name: "Newark Liberty Intl", city: "New York/Newark" },
    ],
    "chicago": [
        { code: "ORD", name: "O'Hare Intl", city: "Chicago" },
        { code: "MDW", name: "Midway Intl", city: "Chicago" },
    ],
    "los angeles": [
        { code: "LAX", name: "Los Angeles Intl", city: "Los Angeles" },
        { code: "BUR", name: "Hollywood Burbank Airport", city: "Burbank" },
    ],
    "miami": [
        { code: "MIA", name: "Miami Intl", city: "Miami" },
        { code: "FLL", name: "Fort Lauderdale-Hollywood Intl", city: "Fort Lauderdale" },
    ],
    "dallas": [
        { code: "DFW", name: "Dallas/Fort Worth Intl", city: "Dallas" },
        { code: "DAL", name: "Dallas Love Field", city: "Dallas" },
    ],
    "houston": [
        { code: "IAH", name: "George Bush Intercontinental", city: "Houston" },
        { code: "HOU", name: "William P. Hobby Airport", city: "Houston" },
    ],
    "san francisco": [
        { code: "SFO", name: "San Francisco Intl", city: "San Francisco" },
        { code: "OAK", name: "Oakland Intl", city: "Oakland" },
    ],
    "seattle": [
        { code: "SEA", name: "Seattle-Tacoma Intl", city: "Seattle" },
    ],
    "boston": [
        { code: "BOS", name: "Logan Intl", city: "Boston" },
    ],
    "las vegas": [
        { code: "LAS", name: "Harry Reid Intl", city: "Las Vegas" },
    ],
    "orlando": [
        { code: "MCO", name: "Orlando Intl", city: "Orlando" },
    ],
    "denver": [
        { code: "DEN", name: "Denver Intl", city: "Denver" },
    ],
    "phoenix": [
        { code: "PHX", name: "Phoenix Sky Harbor Intl", city: "Phoenix" },
    ],
    "washington": [
        { code: "IAD", name: "Dulles Intl", city: "Washington DC" },
        { code: "DCA", name: "Ronald Reagan Washington National", city: "Washington DC" },
    ],
    "minneapolis": [
        { code: "MSP", name: "Minneapolis-Saint Paul Intl", city: "Minneapolis" },
    ],
    "detroit": [
        { code: "DTW", name: "Detroit Metropolitan Wayne County", city: "Detroit" },
    ],
    "charlotte": [
        { code: "CLT", name: "Charlotte Douglas Intl", city: "Charlotte" },
    ],
    "portland": [
        { code: "PDX", name: "Portland Intl", city: "Portland" },
    ],
    "nashville": [
        { code: "BNA", name: "Nashville Intl", city: "Nashville" },
    ],
    "usa": [
        { code: "JFK", name: "John F. Kennedy Intl", city: "New York" },
        { code: "LAX", name: "Los Angeles Intl", city: "Los Angeles" },
        { code: "ORD", name: "O'Hare Intl", city: "Chicago" },
        { code: "ATL", name: "Hartsfield-Jackson Intl", city: "Atlanta" },
        { code: "DFW", name: "Dallas/Fort Worth Intl", city: "Dallas" },
        { code: "MIA", name: "Miami Intl", city: "Miami" },
        { code: "SFO", name: "San Francisco Intl", city: "San Francisco" },
        { code: "SEA", name: "Seattle-Tacoma Intl", city: "Seattle" },
        { code: "BOS", name: "Logan Intl", city: "Boston" },
        { code: "LAS", name: "Harry Reid Intl", city: "Las Vegas" },
        { code: "IAD", name: "Dulles Intl", city: "Washington DC" },
        { code: "MCO", name: "Orlando Intl", city: "Orlando" },
        { code: "DEN", name: "Denver Intl", city: "Denver" },
        { code: "PHX", name: "Phoenix Sky Harbor Intl", city: "Phoenix" },
    ],
    "united states": [
        { code: "JFK", name: "John F. Kennedy Intl", city: "New York" },
        { code: "LAX", name: "Los Angeles Intl", city: "Los Angeles" },
        { code: "ORD", name: "O'Hare Intl", city: "Chicago" },
        { code: "ATL", name: "Hartsfield-Jackson Intl", city: "Atlanta" },
        { code: "MIA", name: "Miami Intl", city: "Miami" },
        { code: "SFO", name: "San Francisco Intl", city: "San Francisco" },
        { code: "DFW", name: "Dallas/Fort Worth Intl", city: "Dallas" },
    ],
    // UK
    "united kingdom": [
        { code: "LHR", name: "Heathrow", city: "London" },
        { code: "LGW", name: "Gatwick", city: "London" },
        { code: "STN", name: "Stansted", city: "London" },
        { code: "MAN", name: "Manchester Intl", city: "Manchester" },
        { code: "EDI", name: "Edinburgh Airport", city: "Edinburgh" },
    ],
    "london": [
        { code: "LHR", name: "Heathrow", city: "London" },
        { code: "LGW", name: "Gatwick", city: "London" },
        { code: "STN", name: "Stansted", city: "London" },
        { code: "LCY", name: "London City", city: "London" },
    ],
    // Australia
    "australia": [
        { code: "SYD", name: "Sydney Kingsford Smith", city: "Sydney" },
        { code: "MEL", name: "Melbourne Intl", city: "Melbourne" },
        { code: "BNE", name: "Brisbane Airport", city: "Brisbane" },
        { code: "PER", name: "Perth Airport", city: "Perth" },
        { code: "ADL", name: "Adelaide Airport", city: "Adelaide" },
    ],
    // Canada
    "canada": [
        { code: "YYZ", name: "Toronto Pearson Intl", city: "Toronto" },
        { code: "YVR", name: "Vancouver Intl", city: "Vancouver" },
        { code: "YUL", name: "Montreal-Trudeau Intl", city: "Montreal" },
        { code: "YYC", name: "Calgary Intl", city: "Calgary" },
    ],
    // Japan
    "japan": [
        { code: "NRT", name: "Narita Intl", city: "Tokyo" },
        { code: "HND", name: "Haneda Airport", city: "Tokyo" },
        { code: "KIX", name: "Kansai Intl", city: "Osaka" },
        { code: "NGO", name: "Chubu Centrair Intl", city: "Nagoya" },
        { code: "CTS", name: "New Chitose Airport", city: "Sapporo" },
    ],
    // Germany
    "germany": [
        { code: "FRA", name: "Frankfurt Intl", city: "Frankfurt" },
        { code: "MUC", name: "Munich Airport", city: "Munich" },
        { code: "BER", name: "Berlin Brandenburg Intl", city: "Berlin" },
        { code: "DUS", name: "Düsseldorf Intl", city: "Düsseldorf" },
    ],
    // France
    "france": [
        { code: "CDG", name: "Charles de Gaulle", city: "Paris" },
        { code: "ORY", name: "Orly Airport", city: "Paris" },
        { code: "NCE", name: "Nice Côte d'Azur", city: "Nice" },
        { code: "LYS", name: "Lyon-Saint Exupéry", city: "Lyon" },
    ],
    // UAE
    "uae": [
        { code: "DXB", name: "Dubai Intl", city: "Dubai" },
        { code: "AUH", name: "Zayed Intl", city: "Abu Dhabi" },
        { code: "SHJ", name: "Sharjah Intl", city: "Sharjah" },
    ],
    "dubai": [
        { code: "DXB", name: "Dubai Intl (Terminal 1/2/3)", city: "Dubai" },
        { code: "DWC", name: "Al Maktoum Intl", city: "Dubai South" },
    ],
    // China
    "china": [
        { code: "PEK", name: "Beijing Capital Intl", city: "Beijing" },
        { code: "PKX", name: "Beijing Daxing Intl", city: "Beijing" },
        { code: "PVG", name: "Shanghai Pudong Intl", city: "Shanghai" },
        { code: "SHA", name: "Shanghai Hongqiao Intl", city: "Shanghai" },
        { code: "CAN", name: "Guangzhou Baiyun Intl", city: "Guangzhou" },
        { code: "CTU", name: "Chengdu Tianfu Intl", city: "Chengdu" },
    ],
    // Italy
    "italy": [
        { code: "FCO", name: "Fiumicino (Leonardo da Vinci)", city: "Rome" },
        { code: "MXP", name: "Milano Malpensa", city: "Milan" },
        { code: "VCE", name: "Venice Marco Polo", city: "Venice" },
        { code: "NAP", name: "Naples Intl", city: "Naples" },
        { code: "FLR", name: "Florence Peretola", city: "Florence" },
    ],
    // Spain
    "spain": [
        { code: "MAD", name: "Adolfo Suárez Madrid-Barajas", city: "Madrid" },
        { code: "BCN", name: "Barcelona-El Prat", city: "Barcelona" },
        { code: "AGP", name: "Málaga-Costa del Sol", city: "Málaga" },
        { code: "PMI", name: "Palma de Mallorca", city: "Mallorca" },
    ],
    // Thailand
    "thailand": [
        { code: "BKK", name: "Suvarnabhumi Intl", city: "Bangkok" },
        { code: "DMK", name: "Don Mueang Intl", city: "Bangkok" },
        { code: "HKT", name: "Phuket Intl", city: "Phuket" },
        { code: "CNX", name: "Chiang Mai Intl", city: "Chiang Mai" },
    ],
    // Singapore
    "singapore": [
        { code: "SIN", name: "Changi Airport (T1/T2/T3/T4)", city: "Singapore" },
    ],
    // Indonesia/Bali
    "indonesia": [
        { code: "CGK", name: "Soekarno-Hatta Intl", city: "Jakarta" },
        { code: "DPS", name: "I Gusti Ngurah Rai Intl", city: "Bali/Denpasar" },
        { code: "SUB", name: "Juanda Intl", city: "Surabaya" },
    ],
    "bali": [
        { code: "DPS", name: "I Gusti Ngurah Rai Intl", city: "Denpasar, Bali" },
    ],
    // South Korea
    "south korea": [
        { code: "ICN", name: "Incheon Intl", city: "Seoul" },
        { code: "GMP", name: "Gimpo Intl", city: "Seoul" },
        { code: "PUS", name: "Gimhae Intl", city: "Busan" },
    ],
    // Malaysia
    "malaysia": [
        { code: "KUL", name: "Kuala Lumpur Intl (KLIA)", city: "Kuala Lumpur" },
        { code: "KUL2", name: "klia2 (AirAsia hub)", city: "Kuala Lumpur" },
        { code: "PEN", name: "Penang Intl", city: "Penang" },
    ],
    // Mexico
    "mexico": [
        { code: "MEX", name: "Benito Juárez Intl", city: "Mexico City" },
        { code: "CUN", name: "Cancún Intl", city: "Cancún" },
        { code: "GDL", name: "Miguel Hidalgo Intl", city: "Guadalajara" },
    ],
    // Brazil
    "brazil": [
        { code: "GRU", name: "São Paulo-Guarulhos Intl", city: "São Paulo" },
        { code: "GIG", name: "Rio de Janeiro-Galeão Intl", city: "Rio de Janeiro" },
        { code: "BSB", name: "Brasília Intl", city: "Brasília" },
    ],
    // South Africa
    "south africa": [
        { code: "JNB", name: "O.R. Tambo Intl", city: "Johannesburg" },
        { code: "CPT", name: "Cape Town Intl", city: "Cape Town" },
        { code: "DUR", name: "King Shaka Intl", city: "Durban" },
    ],
    // Egypt
    "egypt": [
        { code: "CAI", name: "Cairo Intl", city: "Cairo" },
        { code: "HRG", name: "Hurghada Intl", city: "Hurghada" },
        { code: "SSH", name: "Sharm el-Sheikh Intl", city: "Sharm el-Sheikh" },
    ],
    // Turkey
    "turkey": [
        { code: "IST", name: "Istanbul Airport", city: "Istanbul" },
        { code: "SAW", name: "Sabiha Gökçen Intl", city: "Istanbul" },
        { code: "AYT", name: "Antalya Airport", city: "Antalya" },
    ],
    // Greece
    "greece": [
        { code: "ATH", name: "Athens Intl (Eleftherios Venizelos)", city: "Athens" },
        { code: "SKG", name: "Thessaloniki Intl", city: "Thessaloniki" },
        { code: "HER", name: "Heraklion Intl", city: "Crete" },
        { code: "JTR", name: "Santorini Airport", city: "Santorini" },
        { code: "CFU", name: "Corfu Intl", city: "Corfu" },
    ],
    // Portugal
    "portugal": [
        { code: "LIS", name: "Humberto Delgado Airport", city: "Lisbon" },
        { code: "OPO", name: "Francisco Sá Carneiro Airport", city: "Porto" },
        { code: "FAO", name: "Faro Airport", city: "Algarve" },
    ],
    // Netherlands
    "netherlands": [
        { code: "AMS", name: "Amsterdam Schiphol", city: "Amsterdam" },
        { code: "RTM", name: "Rotterdam The Hague Airport", city: "Rotterdam" },
    ],
    // City aliases for popular destinations
    "paris": [
        { code: "CDG", name: "Charles de Gaulle", city: "Paris" },
        { code: "ORY", name: "Orly Airport", city: "Paris" },
    ],
    "tokyo": [
        { code: "NRT", name: "Narita Intl", city: "Tokyo" },
        { code: "HND", name: "Haneda Airport", city: "Tokyo" },
    ],
    "delhi": [
        { code: "DEL", name: "Indira Gandhi Intl", city: "New Delhi" },
    ],
    "new delhi": [
        { code: "DEL", name: "Indira Gandhi Intl", city: "New Delhi" },
    ],
    "mumbai": [
        { code: "BOM", name: "Chhatrapati Shivaji Intl", city: "Mumbai" },
    ],
    "bangalore": [
        { code: "BLR", name: "Kempegowda Intl", city: "Bangalore" },
    ],
    "bengaluru": [
        { code: "BLR", name: "Kempegowda Intl", city: "Bangalore" },
    ],
    "hyderabad": [
        { code: "HYD", name: "Rajiv Gandhi Intl", city: "Hyderabad" },
    ],
    "goa": [
        { code: "GOI", name: "Goa Intl (Dabolim)", city: "Goa" },
    ],
    "osaka": [
        { code: "KIX", name: "Kansai Intl", city: "Osaka" },
        { code: "ITM", name: "Osaka Itami", city: "Osaka" },
    ],
    "rome": [
        { code: "FCO", name: "Fiumicino (Leonardo da Vinci)", city: "Rome" },
        { code: "CIA", name: "Rome Ciampino", city: "Rome" },
    ],
    "milan": [
        { code: "MXP", name: "Milano Malpensa", city: "Milan" },
        { code: "LIN", name: "Milano Linate", city: "Milan" },
    ],
    "barcelona": [
        { code: "BCN", name: "Barcelona-El Prat", city: "Barcelona" },
    ],
    "madrid": [
        { code: "MAD", name: "Adolfo Suárez Madrid-Barajas", city: "Madrid" },
    ],
    "amsterdam": [
        { code: "AMS", name: "Amsterdam Schiphol", city: "Amsterdam" },
    ],
    "bangkok": [
        { code: "BKK", name: "Suvarnabhumi Intl", city: "Bangkok" },
        { code: "DMK", name: "Don Mueang Intl", city: "Bangkok" },
    ],
    "phuket": [
        { code: "HKT", name: "Phuket Intl", city: "Phuket" },
    ],
    "kuala lumpur": [
        { code: "KUL", name: "Kuala Lumpur Intl (KLIA)", city: "Kuala Lumpur" },
    ],
    "seoul": [
        { code: "ICN", name: "Incheon Intl", city: "Seoul" },
        { code: "GMP", name: "Gimpo Intl", city: "Seoul" },
    ],
    "istanbul": [
        { code: "IST", name: "Istanbul Airport", city: "Istanbul" },
        { code: "SAW", name: "Sabiha Gökçen Intl", city: "Istanbul" },
    ],
    "athens": [
        { code: "ATH", name: "Athens Intl (Eleftherios Venizelos)", city: "Athens" },
    ],
    "santorini": [
        { code: "JTR", name: "Santorini Airport", city: "Santorini" },
    ],
    "cairo": [
        { code: "CAI", name: "Cairo Intl", city: "Cairo" },
    ],
    "toronto": [
        { code: "YYZ", name: "Toronto Pearson Intl", city: "Toronto" },
    ],
    "vancouver": [
        { code: "YVR", name: "Vancouver Intl", city: "Vancouver" },
    ],
    "sydney": [
        { code: "SYD", name: "Sydney Kingsford Smith", city: "Sydney" },
    ],
    "melbourne": [
        { code: "MEL", name: "Melbourne Intl", city: "Melbourne" },
    ],
    "beijing": [
        { code: "PEK", name: "Beijing Capital Intl", city: "Beijing" },
        { code: "PKX", name: "Beijing Daxing Intl", city: "Beijing" },
    ],
    "shanghai": [
        { code: "PVG", name: "Shanghai Pudong Intl", city: "Shanghai" },
        { code: "SHA", name: "Shanghai Hongqiao Intl", city: "Shanghai" },
    ],
    "cancun": [
        { code: "CUN", name: "Cancún Intl", city: "Cancún" },
    ],
    "lisbon": [
        { code: "LIS", name: "Humberto Delgado Airport", city: "Lisbon" },
    ],
    "frankfurt": [
        { code: "FRA", name: "Frankfurt Intl", city: "Frankfurt" },
    ],
    "munich": [
        { code: "MUC", name: "Munich Airport", city: "Munich" },
    ],
    "berlin": [
        { code: "BER", name: "Berlin Brandenburg Intl", city: "Berlin" },
    ],
    "johannesburg": [
        { code: "JNB", name: "O.R. Tambo Intl", city: "Johannesburg" },
    ],
    "cape town": [
        { code: "CPT", name: "Cape Town Intl", city: "Cape Town" },
    ],
    "abu dhabi": [
        { code: "AUH", name: "Zayed Intl", city: "Abu Dhabi" },
    ],
    "nice": [
        { code: "NCE", name: "Nice Côte d'Azur", city: "Nice" },
    ],
    "venice": [
        { code: "VCE", name: "Venice Marco Polo", city: "Venice" },
    ],
    "florence": [
        { code: "FLR", name: "Florence Peretola", city: "Florence" },
    ],
    "edinburgh": [
        { code: "EDI", name: "Edinburgh Airport", city: "Edinburgh" },
    ],
    "manchester": [
        { code: "MAN", name: "Manchester Intl", city: "Manchester" },
    ],
    "jakarta": [
        { code: "CGK", name: "Soekarno-Hatta Intl", city: "Jakarta" },
    ],
};

// Get airports for a destination
function getAirportsForDestination(destination) {
    if (!destination) return [];
    const dest = destination.toLowerCase().trim();
    if (dest.length < 2) return [];

    // Direct key match
    if (AIRPORT_DATA[dest]) return AIRPORT_DATA[dest];

    // Partial key match
    for (const [key, airports] of Object.entries(AIRPORT_DATA)) {
        if (dest.includes(key) || key.includes(dest)) {
            return airports;
        }
    }

    // Search by city name within airport objects (e.g., typing "delhi" finds DEL under "india")
    const matches = [];
    const seen = new Set();
    for (const airports of Object.values(AIRPORT_DATA)) {
        for (const airport of airports) {
            const cityLower = airport.city.toLowerCase();
            const cityBase = cityLower.split(',')[0].trim();
            if (cityLower.includes(dest) || dest.includes(cityBase) || cityBase.includes(dest)) {
                if (!seen.has(airport.code)) {
                    seen.add(airport.code);
                    matches.push(airport);
                }
            }
        }
    }
    return matches;
}
