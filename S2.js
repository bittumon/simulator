// Global variables
let map;
let drawingManager;
let selectedPolygon = null;
let autocomplete;
let selectedPlace = null;

// Show only the first step initially
document.addEventListener('DOMContentLoaded', function() {
    // Hide all sections except the first one
    const sections = document.querySelectorAll('.section-step');
    sections.forEach((section, index) => {
        if (index !== 0) {
            section.style.display = 'none';
        }
    });

    // Set up error message close button
    const closeBtn = document.querySelector('.error-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            document.getElementById('address-error-container').style.display = 'none';
        });
    }

    // Set up event listeners for step navigation
    const step1NextBtn = document.getElementById('step1Next');
    if (step1NextBtn) {
        step1NextBtn.addEventListener('click', goToStep2);
    }

    const step2NextBtn = document.getElementById('step2Next');
    if (step2NextBtn) {
        step2NextBtn.addEventListener('click', goToStep3);
    }

    const step3NextBtn = document.getElementById('step3Next');
    if (step3NextBtn) {
        step3NextBtn.addEventListener('click', goToStep4);
    }

    // Set up the start design button functionality
    const startDesignBtn = document.getElementById('startDesign');
    if (startDesignBtn) {
        startDesignBtn.addEventListener('click', startDrawing);
    }

    // Set up the redo button functionality
    const redoBtn = document.getElementById('redoButton');
    if (redoBtn) {
        redoBtn.addEventListener('click', redrawPolygon);
        redoBtn.style.display = 'none'; // Hide initially
    }
});

// Initialize Google Maps autocomplete
function initAutocomplete() {
    // Initialize autocomplete for address input
    const addressInput = document.getElementById('address');
    autocomplete = new google.maps.places.Autocomplete(addressInput, {
        types: ['address'],
        componentRestrictions: { country: 'it' }
    });

    // Listen for place selection
    autocomplete.addListener('place_changed', onPlaceChanged);

    // Initialize the map (it will be hidden until step 2)
    initMap();
    
    console.log("Autocomplete initialized successfully for address input");
}

// Handle place selection from autocomplete
function onPlaceChanged() {
    selectedPlace = autocomplete.getPlace();
    
    if (!selectedPlace.geometry) {
        // User didn't select a prediction; reset the input field
        document.getElementById('address').placeholder = 'Inserisci indirizzo';
        document.getElementById('step1Next').style.display = 'none';
        showError('Seleziona un indirizzo valido dalla lista.');
        return;
    }

    // Display the Procedi button when a valid place is selected
    document.getElementById('step1Next').style.display = 'block';
    
    // Hide any previous error
    document.getElementById('address-error-container').style.display = 'none';
}

// Show error message
function showError(message) {
    const errorContainer = document.getElementById('address-error-container');
    const errorMessage = errorContainer.querySelector('p');
    errorMessage.textContent = message;
    errorContainer.style.display = 'flex';
}

// Navigation functions
function goToStep2() {
    if (!selectedPlace) {
        showError('Seleziona un indirizzo valido prima di procedere.');
        return;
    }
    
    // Hide step 1, show step 2
    document.getElementById('section-step1').style.display = 'none';
    document.getElementById('section-step2').style.display = 'block';
    
    // Center the map on the selected place
    map.setCenter(selectedPlace.geometry.location);
    map.setZoom(20); // Close zoom to see building details
    
    // Force map resize to prevent rendering issues
    google.maps.event.trigger(map, 'resize');
}

function goToStep3() {
    document.getElementById('section-step2').style.display = 'none';
    document.getElementById('section-step3').style.display = 'block';
}

function goToStep4() {
    document.getElementById('section-step3').style.display = 'none';
    document.getElementById('section-step4').style.display = 'block';
}

// Initialize Google Map
function initMap() {
    // Default center (Italy)
    const defaultCenter = { lat: 41.9028, lng: 12.4964 };
    
    // Create a map instance
    map = new google.maps.Map(document.getElementById('map'), {
        center: defaultCenter,
        zoom: 6,
        mapTypeId: 'satellite',
        mapTypeControl: true,
        mapTypeControlOptions: {
            style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
            position: google.maps.ControlPosition.TOP_RIGHT
        }
    });

    // Initialize the drawing manager
    drawingManager = new google.maps.drawing.DrawingManager({
        drawingMode: null, // Initially not in drawing mode
        drawingControl: false, // We'll use our own button
        polygonOptions: {
            fillColor: '#FF0000',
            fillOpacity: 0.3,
            strokeWeight: 2,
            strokeColor: '#FF0000',
            editable: true,
            draggable: false
        }
    });
    
    // Add the drawing manager to the map
    drawingManager.setMap(map);
    
    // Add an event listener for when a polygon is completed
    google.maps.event.addListener(drawingManager, 'polygoncomplete', function(polygon) {
        // Store the selected polygon
        if (selectedPolygon) {
            selectedPolygon.setMap(null); // Clear previous polygon
        }
        selectedPolygon = polygon;
        
        // Calculate and display the area
        updatePolygonArea(polygon);
        
        // Add listeners for when the polygon is modified
        google.maps.event.addListener(polygon.getPath(), 'set_at', function() {
            updatePolygonArea(polygon);
        });
        google.maps.event.addListener(polygon.getPath(), 'insert_at', function() {
            updatePolygonArea(polygon);
        });
        
        // Exit drawing mode
        drawingManager.setDrawingMode(null);
        
        // Show the redo button and Procedi button
        document.getElementById('redoButton').style.display = 'block';
        document.getElementById('step2Next').style.display = 'block';
        
        // Hide the overlay
        document.getElementById('mapOverlay').style.display = 'none';
    });
}

// Start polygon drawing
function startDrawing() {
    // Clear any existing polygon
    if (selectedPolygon) {
        selectedPolygon.setMap(null);
        selectedPolygon = null;
    }
    
    // Enter polygon drawing mode
    drawingManager.setDrawingMode(google.maps.drawing.OverlayType.POLYGON);
    
    // Hide the overlay
    document.getElementById('mapOverlay').style.display = 'none';
    
    // Hide the Procedi button until drawing is complete
    document.getElementById('step2Next').style.display = 'none';
}

// Redraw polygon
function redrawPolygon() {
    // Clear existing polygon
    if (selectedPolygon) {
        selectedPolygon.setMap(null);
        selectedPolygon = null;
    }
    
    // Reset area display
    document.getElementById('areaValue').textContent = '0';
    document.getElementById('step-box-area-value').textContent = '0';
    document.getElementById('area').style.display = 'none';
    
    // Enter drawing mode again
    startDrawing();
}

// Calculate and display the polygon area
function updatePolygonArea(polygon) {
    // Calculate the area
    const area = google.maps.geometry.spherical.computeArea(polygon.getPath());
    const areaInSquareMeters = Math.round(area);
    
    // Display the area
    document.getElementById('areaValue').textContent = areaInSquareMeters;
    document.getElementById('step-box-area-value').textContent = areaInSquareMeters;
    document.getElementById('area').style.display = 'block';
}

// Helper function for toggle buttons in step 3
function selectToggle(button, groupId) {
    // Get all buttons in the group
    const buttons = document.querySelectorAll(`#${groupId} .btn-toggle`);
    
    // Remove active class from all buttons
    buttons.forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Add active class to clicked button
    button.classList.add('active');
}

// Function to highlight checkbox when checked
function highlightCheckbox(checkbox) {
    const label = checkbox.parentElement;
    if (checkbox.checked) {
        label.classList.add('checked');
    } else {
        label.classList.remove('checked');
    }
}