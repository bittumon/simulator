// Clear all localStorage values before the page loads
window.onload = function() {
    console.log("Clearing localStorage...");
    localStorage.clear();
};


    // Shared Variables and DOM Elements
    const steps = document.querySelectorAll(".step");
    const statusBar = document.querySelectorAll(".status-bar div");
    const addressInput = document.getElementById("address");
    const addressUpdateInput = document.getElementById("address-update");
    const step1Next = document.getElementById("step1Next");
    const mapOverlay = document.getElementById("mapOverlay");
    const startDesign = document.getElementById("startDesign");
    const redoButton = document.getElementById("redoButton");
    const areaValue = document.getElementById("areaValue");
    const step2Next = document.getElementById("step2Next");
    const step3Next = document.getElementById("step3Next");
    const imagesContainer = document.getElementById("imagesContainer");

    let map, drawingManager, polygons = [];
    let totalArea = 0;
    let latitude, longitude;

    // Step Navigation Logic
    function goToStep(currentStep, nextStep) {
    if (!steps[currentStep] || !steps[nextStep]) {
        console.error(`Invalid step indices: currentStep=${currentStep}, nextStep=${nextStep}`);
        return;
    }

    // Validate nextStep for statusBar
    if (nextStep < 0 || nextStep >= statusBar.length) {
        console.error(`Invalid nextStep for statusBar: nextStep=${nextStep}`);
        return;
    }

    // Navigate between steps
    steps[currentStep].classList.remove("active");
    steps[currentStep].classList.add("hidden");
    steps[nextStep].classList.add("active");
    steps[nextStep].classList.remove("hidden");

    // Update status bar
    statusBar[currentStep].classList.add("inactive");
    statusBar[nextStep].classList.remove("inactive");

    // Initialize Map in Step 2
    if (nextStep === 1) {
        setTimeout(() => initMap(latitude, longitude), 500);
        addressUpdateInput.value = localStorage.getItem("address") || "";
    }

    // Initialize Step 4
    if (nextStep === 3) {
        initializeStep4();
    }
   }


    // Step 1: Initialize Google Places Autocomplete
    function initAutocomplete() {
        const autocomplete = new google.maps.places.Autocomplete(addressInput);
        autocomplete.addListener("place_changed", function () {
            const place = autocomplete.getPlace();
            if (place.geometry) {
                latitude = place.geometry.location.lat();
                longitude = place.geometry.location.lng();
                step1Next.style.display = "block";
            } else {
                alert("Seleziona un'indrizzio.");
            }
        });
    }

    step1Next.addEventListener("click", function () {
        if (latitude && longitude) {
            localStorage.setItem("latitude", latitude);
            localStorage.setItem("longitude", longitude);
            localStorage.setItem("address", addressInput.value);
            goToStep(0, 1);
        } else {
            alert("Please select a valid address before proceeding.");
        }
    });

    // Step 2: Initialize Map
    function initMap(lat, lng) {
        map = new google.maps.Map(document.getElementById("map"), {
            center: { lat: lat, lng: lng },
            zoom: 20,
            mapTypeId: "satellite",
            tilt: 0,
            fullscreenControl: false,
            streetViewControl: false,
            rotateControl: false,
            mapTypeControl: false
        });

        drawingManager = new google.maps.drawing.DrawingManager({
            drawingControl: true,
            drawingControlOptions: {
                drawingModes: ["polygon"]
            },
            polygonOptions: {
                editable: true,
                draggable: true,
                fillColor: "#ff0000",
                fillOpacity: 0.3,
                strokeWeight: 3
            }
        });

        drawingManager.setMap(map);

        google.maps.event.addListener(drawingManager, "overlaycomplete", function (event) {
            const polygon = event.overlay;
            polygons.push(polygon);

            totalArea = polygons.reduce((sum, poly) => {
                return sum + google.maps.geometry.spherical.computeArea(poly.getPath());
            }, 0);

            console.log(`Calculated total area: ${totalArea}`);
            areaValue.innerText = totalArea.toFixed(2);
            localStorage.setItem("area", totalArea.toFixed(2));
            document.getElementById("area").style.display = "block";
            step2Next.style.display = "block";
        });
    }

    step2Next.addEventListener("click", function () {
        goToStep(1, 2);
    });

    redoButton.addEventListener("click", function () {
        polygons.forEach(polygon => polygon.setMap(null));
        polygons = [];
        totalArea = 0;
        areaValue.innerText = "0";
        localStorage.setItem("area", "0");
        document.getElementById("area").style.display = "none";
        step2Next.style.display = "none";
    });

    startDesign.addEventListener("click", function () {
        mapOverlay.style.display = "none";
    });

    window.onload = initAutocomplete;

    // Step 3 Logic
    const consumoSlider = document.getElementById("consumoSlider");
    const sliderValue = document.getElementById("sliderValue");
    const prevalenzaSlider = document.getElementById("prevalenzaSlider");
    const prevalenzaValue = document.getElementById("prevalenzaValue");
    const logos = document.querySelectorAll(".logo");
    const efficiencyCheckboxes = document.querySelectorAll(".efficiency-checkbox");

    let costo_bolletta = null;
    let inclinazione = null;
    let prevalenza = null;
    let selectedOptions = [];
    let azimuth = null;

    consumoSlider.addEventListener("input", () => {
        sliderValue.textContent = `${consumoSlider.value} €`;
        costo_bolletta = parseFloat(consumoSlider.value);
        checkStep3Completion();
    });

    prevalenzaSlider.addEventListener("input", () => {
        prevalenzaValue.textContent = `${prevalenzaSlider.value}%`;
        prevalenza = parseFloat(prevalenzaSlider.value);
        checkStep3Completion();
    });



logos.forEach((logo) => {
    logo.addEventListener("click", () => {
        // Remove active class from all logos
        logos.forEach((l) => l.classList.remove("active-logo"));

        // Highlight selected logo
        logo.classList.add("active-logo");

        // Assign inclinazione and azimuth
        inclinazione = parseInt(logo.getAttribute("data-inclinazione"), 10);
        azimuth = parseInt(logo.getAttribute("data-azimuth"), 10);

        console.log(`Selected inclinazione: ${inclinazione}, azimuth: ${azimuth}`);
        checkStep3Completion();
    });
});

    // Efficiency checkbox functionality
// Efficiency checkbox functionality
    efficiencyCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", () => {
            const imgUrl = checkbox.getAttribute("data-img");

            // Create or remove the image dynamically
            let existingImage = Array.from(imagesContainer.children).find(
                (img) => img.getAttribute("src") === imgUrl
            );

            if (checkbox.checked) {
                if (!existingImage) {
                    const imgElement = document.createElement("img");
                    imgElement.setAttribute("src", imgUrl);
                    imgElement.style.width = "100px";
                    imgElement.style.margin = "10px";
                    imgElement.style.background = "transparent"; // Ensure transparency
                    imgElement.style.cursor = "move";

                    imagesContainer.appendChild(imgElement);
                }
            } else {
                if (existingImage) existingImage.remove(); // Remove if it exists
            }
        });
    });

    // Check if Step 3 is complete
    function checkStep3Completion() {
        if (costo_bolletta && inclinazione && prevalenza !== null) {
            step3Next.style.display = "block"; // Show "Next" button
        } else {
            step3Next.style.display = "none"; // Hide "Next" button
        }
    }



    function checkStep3Completion() {
        if (costo_bolletta && inclinazione && prevalenza !== null) {
            step3Next.style.display = "block";
        } else {
            step3Next.style.display = "none";
        }
    }

    step3Next.addEventListener("click", () => {
        localStorage.setItem("consumo", costo_bolletta);
        localStorage.setItem("inclinazione", inclinazione);
        localStorage.setItem("azimuth", azimuth);
        localStorage.setItem("prevalenza", prevalenza);
        localStorage.setItem("efficiencyOptions", JSON.stringify(selectedOptions));
        goToStep(2, 3);
    });

    // Step 4 Logic
// JSON Data
const potten = ["3.32", "4.15", "4.98", "6.23", "8.30"]
const batt = {
    "3.32": { "no_accumulo": "7150,00", "5Kwaccum": "12000,00", "10Kwaccum": "15000,00" },
    "4.15": { "no_accumulo": "7800,00", "5Kwaccum": "12500,00", "10Kwaccum": "15400,00" },
    "4.98": { "no_accumulo": "8550,00", "5Kwaccum": "13300,00", "10Kwaccum": "16150,00" },
    "6.23": { "no_accumulo": "9650,00", "5Kwaccum": "14300,00", "10Kwaccum": "17150,00", "15Kwaccum": "19900,00" },
    "8.30": { "no_accumulo": "11400,00", "5Kwaccum": "16000,00", "10Kwaccum": "18900,00", "15Kwaccum": "21800,00", "20Kwaccum": "25550,00" }
};

const default_batt = {
    "40": { "3.32": "7150,00", "4.15": "16000,00", "4.98": "8550,00", "6.23": "9650,00", "8.30": "11400,00" },
    "50": { "3.32": "7150,00", "4.15": "16000,00", "4.98": "8550,00", "6.23": "14300,00", "8.30": "16000,00" },
    "60": { "3.32": "12500,00", "4.15": "16000,00", "4.98": "13300,00", "6.23": "17150,00", "8.30": "18900,00" },
    "70": { "3.32": "15000,00", "4.15": "15400,00", "4.98": "16150,00", "6.23": "19900", "8.30": "21800,00" },
    "80": { "3.32": "15000,00", "4.15": "15400,00", "4.98": "16150,00", "6.23": "19900", "8.30": "25550,00" }
};

// Calculate Potenza Based on Area
function calculatePotenza(area) {
    if (area >= 16 && area < 20) return "3.32";
    if (area >= 20 && area < 24) return "4.15";
    if (area >= 24 && area < 30) return "4.98";
    if (area >= 30 && area < 40) return "6.23";
    if (area >= 40) return "8.30";
    return null;
}

// Calculate Default Battery Cost
function calculateDefaultBatteryCost(night, potenza) {
    if (night <= 39) return default_batt["40"][potenza];
    if (night >= 40 && night <= 49) return default_batt["50"][potenza];
    if (night >= 50 && night <= 69) return default_batt["50"][potenza];
    if (night >= 70 && night <= 89) return default_batt["70"][potenza];
    return default_batt["80"][potenza];
}


;


// Step 4 Initialization

async function initializeStep4() {
    console.log("Initializing Step 4...");

    const latitude = localStorage.getItem("latitude") || "N/A";
    const longitude = localStorage.getItem("longitude") || "N/A";
    const address = localStorage.getItem("address") || "N/A";
    const area = parseFloat(localStorage.getItem("area") || 0).toFixed(2);
    const azimuth = localStorage.getItem("azimuth") || "N/A";
    const consumo = parseFloat(localStorage.getItem("consumo") || 0).toFixed(2);
    const prevalenza = parseFloat(localStorage.getItem("prevalenza") || 0);
    const inclinazione = localStorage.getItem("inclinazione") || "N/A";
    const night = prevalenza ? 100 - prevalenza : "N/A";
    const efficiencyOptions = JSON.parse(localStorage.getItem("efficiencyOptions")) || [];
    const additionalImagesContainer = document.getElementById("additionalImagesContainer");
    const batteryImagesContainer = document.getElementById("batteryImagesContainer");


    let potenza = calculatePotenza(area);
    let baseCost = parseFloat(batt[potenza]?.no_accumulo || "0");
    let additionalOptionsCost = 0;
    let chartInstance = null; // To store the chart instance globally

    let produzione_annui_totali = 0;
    let basemonthlyData = []; // Array to store monthly production values
    const months = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio",
        "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre",
        "Novembre", "Dicembre"
    ];

    // Update HTML Elements
    document.getElementById("addressResult").textContent = address;
    document.getElementById("latitudeResult").textContent = latitude;
    document.getElementById("longitudeResult").textContent = longitude;
    document.getElementById("areaResult").textContent = `${area} m²`;
    document.getElementById("azimuthResult").textContent = `${azimuth}°`;
    document.getElementById("consumoResult").textContent = `${consumo} €`;
    document.getElementById("inclinazioneResult").textContent = `${inclinazione}°`;
    document.getElementById("prevalenzaResult").textContent = `${prevalenza}%`;
    document.getElementById("nightResult").textContent = `${night}%`;
    document.getElementById("potenzaResult").textContent = `${potenza} kW`;
    document.getElementById("costResult").textContent = `${baseCost.toFixed(2)} €`;

    document.getElementById('needStorage').addEventListener('click', function () {
    const dropdownContainer = document.getElementById('storageDropdownContainer');
    const batteryImagesContainer = document.getElementById('batteryImagesContainer');

    // Toggle visibility of the dropdown container
    const isHidden = dropdownContainer.style.display === 'none';
    dropdownContainer.style.display = isHidden ? 'block' : 'none';

    // Clear battery images when the dropdown is hidden
    if (!isHidden) {
        batteryImagesContainer.innerHTML = ""; // Clear all battery images
    }
});

    // Generate Potenza Buttons
    generatePotenzaButtons(potenza);

    // Populate Dropdown with Battery Options
    function populateDropdown(currentPotenza) {
    const storageDropdown = document.getElementById("batteryStorage");
    storageDropdown.innerHTML = ""; // Clear existing options

    if (batt[currentPotenza]) {
        const batteryOptions = batt[currentPotenza];

        // Mapping for user-friendly labels
        const labelMapping = {
            no_accumulo: "0Kw",
            "5Kwaccum": "5Kw",
            "10Kwaccum": "10Kw",
            "15Kwaccum": "15Kw",
            "20Kwaccum": "20Kw"
        };

        Object.keys(batteryOptions).forEach(key => {
            const option = document.createElement("option");
            option.value = key; // Keep the original key as the value
            option.textContent = labelMapping[key] || key; // Use the user-friendly label
            storageDropdown.appendChild(option);
        });

        // Add change event listener to update cost
        storageDropdown.addEventListener("change", () => {
            const selectedKey = storageDropdown.value;
            baseCost = parseFloat(batt[currentPotenza]?.[selectedKey] || "0");
            updateTotalCost();
        });
    }
}

    // Function to Generate Potenza Buttons
    function generatePotenzaButtons(currentPotenza) {
        const potenzaButtonsContainer = document.getElementById("potenzaButtons");
        potenzaButtonsContainer.innerHTML = ""; // Clear existing buttons
    
        const filteredPotten = potten.filter((p) => {
            const currentIndex = potten.indexOf(currentPotenza);
            return Math.abs(potten.indexOf(p) - currentIndex) <= 2;
        });
    
        filteredPotten.forEach((p) => {
            const button = document.createElement("button");
            button.textContent = `${p} kW`;
            button.classList.add("btn", "btn-secondary", "mx-2");
    
            button.addEventListener("click", () => {
                potenza = p; // ✅ Update Potenza
                document.getElementById("potenzaResult").textContent = `${potenza} kW`;
    
                // ✅ Update Base Cost when changing Potenza
                baseCost = parseFloat(batt[potenza]?.no_accumulo || "0");
                console.log(`🔄 Updated Base Cost for ${potenza} kW: ${baseCost.toFixed(2)} €`);
    
                updateTotalCost(); // ✅ Ensure Total Cost is recalculated
                populateDropdown(potenza); // Refresh dropdown
                updateProduzioneAnnuiTotali(potenza); // ✅ Ensure production updates correctly
                calculateAndUpdateResults(); // ✅ Ensure energy calculations update
            });
    
            potenzaButtonsContainer.appendChild(button);
        });
    
        populateDropdown(currentPotenza);
    }

    // Handle additional options cost
    const additionalOptions = document.querySelectorAll(".additional-option");
    additionalOptions.forEach(option => {
        option.addEventListener("change", (event) => {
            const optionCost = parseFloat(event.target.getAttribute("data-cost"));
            if (event.target.checked) {
                additionalOptionsCost += optionCost;
            } else {
                additionalOptionsCost -= optionCost;
            }
            updateTotalCost();
        });
    });

    // Function to Update Total Cost
    function updateTotalCost() {
        const totalCost = baseCost + additionalOptionsCost;
        document.getElementById("costResult").textContent = `${totalCost.toFixed(2)} €`;
        console.log(`🟢 Total Cost Updated: ${totalCost.toFixed(2)} €`);
        
    }
    // Image URLs for additional options
    const additionalOptionsImages = {
        wallbox: "https://www.manutenzione-impianti-fotovoltaici.com/imaggine%20simulator/9.png",
        ottimizzatori: "https://www.manutenzione-impianti-fotovoltaici.com/imaggine%20simulator/8.png",
        piccioni: "https://www.manutenzione-impianti-fotovoltaici.com/imaggine%20simulator/piccioni.png",
        backup: "https://www.manutenzione-impianti-fotovoltaici.com/imaggine%20simulator/1.png",
        "linea-vita": "https://www.manutenzione-impianti-fotovoltaici.com/imaggine%20simulator/2.png",
    };

    // Image URL for battery
    const singleBatteryImage = "https://www.manutenzione-impianti-fotovoltaici.com/imaggine%20simulator/11.png";

    // Handle additional options image updates
    function updateAdditionalOptionImages() {
        additionalImagesContainer.innerHTML = ""; // Clear container
        additionalOptions.forEach(option => {
            if (option.checked) {
                const img = document.createElement("img");
                img.src = additionalOptionsImages[option.id];
                additionalImagesContainer.appendChild(img);
            }
        });
    }

    // Add event listeners for additional options
    additionalOptions.forEach(option => {
        option.addEventListener("change", updateAdditionalOptionImages);
    });

    // Handle battery image updates
    const storageDropdown = document.getElementById("batteryStorage");
    storageDropdown.addEventListener("change", () => {
        const selectedValue = storageDropdown.value;
        const numberOfBatteries = selectedValue === "no_accumulo" ? 0 : parseInt(selectedValue.replace("Kwaccum", "")) / 5;

        batteryImagesContainer.innerHTML = ""; // Clear container
        for (let i = 0; i < numberOfBatteries; i++) {
            const img = document.createElement("img");
            img.src = singleBatteryImage;
            batteryImagesContainer.appendChild(img);
        }
    });

    // Call the functions initially to set up any pre-selected options
    updateAdditionalOptionImages();
    storageDropdown.dispatchEvent(new Event("change")); // Initialize battery images

let detrazione = 36; // Default value for detrazione

// Add event listener for the "Primo Casa" checkbox
document.getElementById("primo-casa").addEventListener("change", function (event) {
    if (event.target.checked) {
        detrazione = 50; // If "Primo Casa" is selected
    } else {
        detrazione = 36; // If "Primo Casa" is deselected
    }
    console.log(`Detrazione set to ${detrazione}%`); // Debugging output
});


// Function to update Produzione Annui Totali and the Graph
function updateProduzioneAnnuiTotali(selectedPotenza) {
    if (!Array.isArray(baseMonthlyData) || baseMonthlyData.length !== 12) {
        console.error("❌ Error: baseMonthlyData is not valid or missing API response.");
        return;
    }

    // ✅ Correctly update `monthlyData` using the selected potenza
    monthlyData = baseMonthlyData.map(value => value * selectedPotenza);

    // ✅ Correctly update `produzione_annui_totali`
    produzione_annui_totali = monthlyData.reduce((sum, value) => sum + value, 0);

    console.log(`🔄 Potenza changed to: ${selectedPotenza} kW`);
    console.log("📊 Updated Monthly Data:", monthlyData);
    console.log("✅ New Total Annual Production:", produzione_annui_totali.toFixed(2), "kWh");

    // ✅ Update UI with the correct total production value
    document.getElementById("produzioneAnnuiTotali").textContent = `${produzione_annui_totali.toFixed(2)} kWh`;

    // ✅ Update the graph
    plotEnergyGraph();

}

// Fetch PVWatts API data
async function fetchPVWattsData() {
    const apiUrl = `https://developer.nrel.gov/api/pvwatts/v8.json?api_key=q8FeOId3P75qkcCNJLYVWccY2jHBF23XooQpl9Mx&azimuth=${azimuth}&tilt=${inclinazione}&system_capacity=1&dataset=nsrdb&albedo=0.3&bifaciality=0.7&format=json&module_type=0&losses=14&array_type=1&use_wf_albedo=1&lat=${latitude}&lon=${longitude}`;

    try {
        const response = await fetch(apiUrl);
        const data = await response.json();

        if (data && data.outputs && data.outputs.ac_monthly) {
            baseMonthlyData = data.outputs.ac_monthly; // Store values for 1 kW
            console.log("📊 API Data for 1 kW:", baseMonthlyData);

            // Update initial production with default potenza
            updateProduzioneAnnuiTotali(potenza);
        } else {
            console.error("❌ Invalid API response format:", data);
        }
    } catch (error) {
        console.error("⚠️ Error fetching PVWatts data:", error);
    }
}



    // Plot energy graph
function plotEnergyGraph() {
    const canvasContainer = document.getElementById("energyGraphContainer");
    canvasContainer.innerHTML = ""; // Clear existing graph container

    const canvas = document.createElement("canvas");
    canvasContainer.appendChild(canvas);

    const ctx = canvas.getContext("2d");
    const monthlyValues = monthlyData.map(value => value * potenza); // Multiply energy by potenza

    // Destroy existing chart instance if it exists
    if (chartInstance) {
        chartInstance.destroy();
    }

    // Create a new chart
    chartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: [
                "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio",
                "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre",
                "Novembre", "Dicembre"
            ],
            datasets: [{
                label: "Produzione Energetica (kWh)",
                data: monthlyData,
                backgroundColor: "rgba(75, 192, 192, 0.6)",
                borderColor: "rgba(75, 192, 192, 1)",
                borderWidth: 1
                
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}




function calculateAndUpdateResults() {
    // Capture inputs and selections
    const consumoResult = parseFloat(localStorage.getItem("consumo") || 0);
    const accumulo = parseInt(storageDropdown.value.replace("Kwaccum", "")) || 0;
    const prezzo_aggiuntivo_wallbox = document.getElementById("wallbox").checked ? 1500 : 0;
    const prezzo_aggiuntivo_ottimizzatori = document.getElementById("ottimizzatori").checked ? 720 : 0;
    const prezzo_aggiuntivo_backup = document.getElementById("backup").checked ? 1000 : 0;
    const prezzo_aggiuntivo_piccioni = document.getElementById("piccioni").checked ? 320 : 0;
    const prezzo_aggiuntivo_linea_vita = document.getElementById("linea-vita").checked ? 2200 : 0;

    // Calculations
    const consumi_annui = (consumoResult / 0.35) * 12;
    const consumi_annui_giorno = consumi_annui * (1 - (night / 100));
    const consumi_annui_notte = consumi_annui * (night / 100);


    const autoconsumo_diretto_kwh_anno_1 = Math.min(
        consumi_annui_giorno * (1 - (night / 100)) +
        consumi_annui_notte * (night / 100),
        produzione_annui_totali
    ) * 0.90;

    const autoconsumo_batteria_kwh_anno_1 = Math.min(
        consumi_annui_notte * (1 - (night / 100)) +
        consumi_annui_giorno * (night / 100),
        accumulo * 365 * 0.75
    );

    const autoconsumo_totale_kwh_anno_1 = autoconsumo_batteria_kwh_anno_1 + autoconsumo_diretto_kwh_anno_1;
    const autoconsumo_percentuale = (autoconsumo_totale_kwh_anno_1 / produzione_annui_totali) * 100;

    const immissione_kwh_anno_1 = produzione_annui_totali - autoconsumo_totale_kwh_anno_1;
    const prelievo_rete_dopo_impianto_anno_1 = consumi_annui - autoconsumo_totale_kwh_anno_1;

    const costo_mensile_bolletta_dopo_impianto = (prelievo_rete_dopo_impianto_anno_1 * 0.35 / 12) * 1.2;
    const risparmio_1_anno_bolletta = (consumoResult - costo_mensile_bolletta_dopo_impianto) * 12 * 0.95;

    const massimale = potenza * 2400 + accumulo * 1000;
    const risparmio_10_anni_detrazione = Math.min(massimale, baseCost) * (detrazione / 100);

    const risparmio_25_anni_totale = risparmio_10_anni_detrazione + risparmio_1_anno_bolletta;

    // Update HTML Elements
    document.getElementById("consumiAnnui").textContent = consumi_annui.toFixed(2);
    document.getElementById("autoconsumoDiretto").textContent = autoconsumo_diretto_kwh_anno_1.toFixed(2);
    document.getElementById("autoconsumoBatteria").textContent = autoconsumo_batteria_kwh_anno_1.toFixed(2);
    document.getElementById("autoconsumoTotale").textContent = autoconsumo_totale_kwh_anno_1.toFixed(2);
    document.getElementById("autoconsumoPercentuale").textContent = autoconsumo_percentuale.toFixed(2);
    document.getElementById("immissione").textContent = immissione_kwh_anno_1.toFixed(2);
    document.getElementById("prelievoRete").textContent = prelievo_rete_dopo_impianto_anno_1.toFixed(2);
    document.getElementById("costoBolletta").textContent = costo_mensile_bolletta_dopo_impianto.toFixed(2);
    document.getElementById("risparmioAnno").textContent = risparmio_1_anno_bolletta.toFixed(2);
    document.getElementById("risparmioDetrazione").textContent = risparmio_10_anni_detrazione.toFixed(2);
    document.getElementById("risparmioTotale").textContent = risparmio_25_anni_totale.toFixed(2);

    document.getElementById("consumiAnnuiGiorno").textContent = consumi_annui_giorno.toFixed(2) + " kWh";
    document.getElementById("consumiAnnuiNotte").textContent = consumi_annui_notte.toFixed(2) + " kWh";
}


// Call `calculateAndUpdateResults` when Potenza or other values are updated
document.querySelectorAll(".potenza-button").forEach(button => {
    button.addEventListener("click", () => {
        potenza = parseFloat(button.textContent);
        calculateAndUpdateResults();
    });
});


function updateAdditionalValues() {
    const consumoResult = parseFloat(localStorage.getItem("consumo") || 0);
    const accumulo = parseInt(storageDropdown.value.replace("Kwaccum", "")) || 0;
    const prezzo_aggiuntivo_wallbox = document.getElementById("wallbox").checked ? 1500 : 0;
    const prezzo_aggiuntivo_ottimizzatori = document.getElementById("ottimizzatori").checked ? 720 : 0;
    const prezzo_aggiuntivo_backup = document.getElementById("backup").checked ? 1000 : 0;
    const prezzo_aggiuntivo_piccioni = document.getElementById("piccioni").checked ? 320 : 0;
    const prezzo_aggiuntivo_linea_vita = document.getElementById("linea-vita").checked ? 2200 : 0;

    // Update HTML Elements
    document.getElementById("consumoResultValue").textContent = consumoResult.toFixed(2);
    document.getElementById("accumuloValue").textContent = accumulo;
    document.getElementById("wallboxValue").textContent = prezzo_aggiuntivo_wallbox.toFixed(2);
    document.getElementById("ottimizzatoriValue").textContent = prezzo_aggiuntivo_ottimizzatori.toFixed(2);
    document.getElementById("backupValue").textContent = prezzo_aggiuntivo_backup.toFixed(2);
    document.getElementById("piccioniValue").textContent = prezzo_aggiuntivo_piccioni.toFixed(2);
    document.getElementById("lineaVitaValue").textContent = prezzo_aggiuntivo_linea_vita.toFixed(2);
}

// Call `updateAdditionalValues` whenever relevant inputs or selections are changed
document.getElementById("wallbox").addEventListener("change", updateAdditionalValues);
document.getElementById("ottimizzatori").addEventListener("change", updateAdditionalValues);
document.getElementById("backup").addEventListener("change", updateAdditionalValues);
document.getElementById("backup").addEventListener("accumulo", updateAdditionalValues);
document.getElementById("piccioni").addEventListener("change", updateAdditionalValues);
document.getElementById("linea-vita").addEventListener("change", updateAdditionalValues);
storageDropdown.addEventListener("change", updateAdditionalValues);




// Fetch API data and initialize
// Call it initially to display default values
updateAdditionalValues();

generatePotenzaButtons(potenza); // Generate potenza buttons
await fetchPVWattsData(); // Fetch data and initialize the chart
updateProduzioneAnnuiTotali(potenza);
updateAdditionalOptionImages(); // Update images
storageDropdown.dispatchEvent(new Event("change"));
calculateAndUpdateResults();

}

// Step 5 Initialization
document.addEventListener('DOMContentLoaded', function () {
    const step4Next = document.getElementById('step4Next');
    const step5 = document.getElementById('step5');
    const contactForm = document.getElementById('contactForm');
    const submitContact = document.getElementById('submitContact');

    const successModal = document.getElementById('successModal');
    const failureModal = document.getElementById('failureModal');
    const downloadPDF = document.getElementById('downloadPDF');
    const restartProcess = document.getElementById('restartProcess');
    const successClose = document.getElementById('successClose');
    const failureClose = document.getElementById('failureClose');


    // Function to get the current timestamp
    function getCurrentTimestamp() {
        return new Date().toISOString();
    }

    // Function to generate a unique report ID
    function generateReportID(firstName, lastName, timestamp) {
        return `RES-${firstName.substring(0, 2).toUpperCase()}${lastName.substring(0, 2).toUpperCase()}-${timestamp}`;
    }



    // Function to go to step 5
    step4Next.addEventListener('click', function () {
        document.querySelector('.step.active').classList.remove('active');
        step5.classList.add('active');
        document.getElementById('status-step4').classList.add('inactive');
        document.getElementById('status-step5').classList.remove('inactive');
    });

    // Form validation
    contactForm.addEventListener('input', function () {
        const isFormValid = contactForm.checkValidity();
        submitContact.disabled = !isFormValid;
    });

    // Form submission
    contactForm.addEventListener('submit', function (event) {
        event.preventDefault();

        const firstName = document.getElementById('firstName').value;
        const lastName = document.getElementById('lastName').value;
        const contactNumber = document.getElementById('contactNumber').value;
        const email = document.getElementById('email').value;
        const tempo = getCurrentTimestamp();
        const rep_file = generateReportID(firstName, lastName, tempo);
        


        // Construct the URL for the Google Forms submission
        const formUrl = `https://docs.google.com/forms/d/e/1FAIpQLSee10XOVRM2hrskYjU3MerIuZI2wp7_Y5FXTILM4JP81_dfqA/formResponse?usp=pp_url`
        + `&entry.164572236=${encodeURIComponent(tempo)}`
        + `&entry.49209369=${encodeURIComponent(firstName)}`
        + `&entry.1372551180=${encodeURIComponent(lastName)}`
        + `&entry.1505658450=${encodeURIComponent(addressResult)}`
        + `&entry.1305223479=${encodeURIComponent(latitudeResult)}`
        + `&entry.1738069916=${encodeURIComponent(contactNumber)}`
        + `&entry.1843687495=${encodeURIComponent(email)}`
        + `&entry.1238272703=${encodeURIComponent(longitudeResult)}`
        + `&entry.1927567924=${encodeURIComponent(areaResult)}`
        + `&entry.1609859917=${encodeURIComponent(consumoResult)}`
        + `&entry.235331739=${encodeURIComponent(inclinazione)}`
        + `&entry.68571336=${encodeURIComponent(prevalenzaResult)}`
        + `&entry.1647761942=${encodeURIComponent(azimuthResult)}`
        + `&entry.1393245675=${encodeURIComponent(nightResult)}`
        + `&entry.1764548391=${encodeURIComponent(efficiencyOptionsResult)}`
        + `&entry.647173530=${encodeURIComponent(potenzaResult)}`
        //+ `&entry.698925198=${encodeURIComponent(costResult)}`
        //+ `&entry.1984739582=${encodeURIComponent()}`
        //+ `&entry.68661976=${encodeURIComponent(detrazione)}`
        + `&entry.918715533=${encodeURIComponent(consumiAnnui)}`
        + `&entry.472438144=${encodeURIComponent(autoconsumoDiretto)}`
        + `&entry.815981441=${encodeURIComponent(autoconsumoBatteria)}`
        + `&entry.1864664582=${encodeURIComponent(autoconsumoTotale)}`
        + `&entry.668099502=${encodeURIComponent(autoconsumoPercentuale)}`
        + `&entry.488621106=${encodeURIComponent(immissione)}`
        + `&entry.997238363=${encodeURIComponent(prelievoRete)}`
        + `&entry.1707183499=${encodeURIComponent(costoBolletta)}`
        + `&entry.722810239=${encodeURIComponent(risparmioAnno)}`
        + `&entry.1949209604=${encodeURIComponent(risparmioDetrazione)}`
        + `&entry.977732916=${encodeURIComponent(risparmioTotale)}`
        + `&entry.104100858=${encodeURIComponent(consumiAnnui)}`
        + `&entry.460881334=${encodeURIComponent(accumuloValue)}`
        + `&entry.1335972009=${encodeURIComponent(wallboxValue)}`
        + `&entry.1356805433=${encodeURIComponent(ottimizzatoriValue)}`
        + `&entry.929000443=${encodeURIComponent(backupValue)}`
        + `&entry.25120544=${encodeURIComponent(piccioniValue)}`
        + `&entry.1949265544=${encodeURIComponent(lineaVitaValue)}`
        + `&entry.774788600=${encodeURIComponent(consumiAnnuiGiorno)}`
        + `&entry.1023535803=${encodeURIComponent(consumiAnnuiNotte)}`
        //+ `&entry.616870084=${encodeURIComponent()}`
        //+ `&entry.1028386922=${encodeURIComponent()}`
        + `&entry.262233617=${encodeURIComponent(rep_file)}`
        
            
            // Add other fields here as needed
            + `&submit=Submit`;

        // Make the POST request to Google Forms
        fetch(formUrl, {
            method: 'POST',
            mode: 'no-cors'
        }).then(response => {
            if (response.status === 200 || response.status === 0) {
                // Show the success modal
                successModal.style.display = 'block';
            } else {
                // Show the failure modal
                failureModal.style.display = 'block';
            }
        }).catch(error => {
            console.error('Error submitting the form:', error);
            // Show the failure modal
            failureModal.style.display = 'block';
        });
    });

    // Function to create and download the PDF report
    function createAndDownloadPDF() {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();

        // Add content to the PDF
        doc.text('Report', 10, 10);
        doc.text(`First Name: ${document.getElementById('firstName').value}`, 10, 20);
        doc.text(`Last Name: ${document.getElementById('lastName').value}`, 10, 30);
        doc.text(`Contact Number: ${document.getElementById('contactNumber').value}`, 10, 40);
        doc.text(`Email: ${document.getElementById('email').value}`, 10, 50);

        // Add other necessary information from Step 4
        // ...

        // Save the PDF
        doc.save('report.pdf');
    }

    // Event listener for downloading the PDF
    downloadPDF.addEventListener('click', function () {
        createAndDownloadPDF();
        successModal.style.display = 'none';
        window.location.reload();
    });

    // Event listener for restarting the process
    restartProcess.addEventListener('click', function () {
        failureModal.style.display = 'none';
        window.location.reload();
    });

    // Close modals when the close button is clicked
    successClose.addEventListener('click', function () {
        successModal.style.display = 'none';
    });
    failureClose.addEventListener('click', function () {
        failureModal.style.display = 'none';
    });

    // Close modals when clicking outside of the modal content
    window.onclick = function (event) {
        if (event.target === successModal) {
            successModal.style.display = 'none';
        }
        if (event.target === failureModal) {
            failureModal.style.display = 'none';
        }
    };
});


