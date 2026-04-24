document.addEventListener("DOMContentLoaded", () => {
    
    // Initialize Canvas Visualizer
    const visualizer = new Fix8Visualizer();
    
    // Bind the visualizer's drag-and-drop to our network API
    visualizer.onFixationUpdate = (index, x, y) => {
        fetch('/api/action/update_fixation', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ index, x, y })
        }).catch(console.error); // Silently sync drift corrections
    };
    
    // UI Elements
    const btnLoadDemo = document.getElementById('btn-load-demo');
    const btnApplyNoise = document.getElementById('btn-apply-noise');
    const noiseSlider = document.getElementById('noise-slider');
    const noiseVal = document.getElementById('noise-val');
    const loader = document.getElementById('loader');
    
    const statusText = document.getElementById('status-text');
    const statusDot = document.getElementById('status-dot');
    const fixCount = document.getElementById('fix-count');
    
    // State
    let hasData = false;
    
    // Utilities
    const showLoader = () => loader.classList.add('active');
    const hideLoader = () => loader.classList.remove('active');
    
    const setStatus = (msg, dotColor = '#22c55e') => {
        statusText.innerText = msg;
        statusDot.style.background = dotColor;
        statusDot.style.boxShadow = `0 0 8px ${dotColor}`;
    };

    const updateControls = () => {
        btnApplyNoise.disabled = !hasData;
        if (!hasData) {
            btnApplyNoise.style.opacity = '0.5';
            btnApplyNoise.style.cursor = 'not-allowed';
        } else {
            btnApplyNoise.style.opacity = '1';
            btnApplyNoise.style.cursor = 'pointer';
        }
    };
    
    // Fetch initial state just in case session already exists
    fetch('/api/state')
        .then(res => res.json())
        .then(data => {
            if (data.has_data) {
                handleStateUpdate(data);
                setStatus("Restored Session", "#38bdf8");
            } else {
                updateControls();
            }
        });

    // Event Listeners
    noiseSlider.addEventListener('input', (e) => {
        noiseVal.innerText = e.target.value;
    });
    
    btnLoadDemo.addEventListener('click', () => {
        showLoader();
        setStatus("Loading Data...", "#fbbf24");
        
        fetch('/api/load_demo', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        })
        .then(res => res.json())
        .then(data => {
            hideLoader();
            if (data.error) {
                alert("Error loading demo: " + data.error);
                setStatus("Error", "#ef4444");
                return;
            }
            handleStateUpdate(data.state);
            setStatus("Demo Loaded");
        })
        .catch(err => {
            hideLoader();
            console.error(err);
            setStatus("Network Error", "#ef4444");
        });
    });
    
    btnApplyNoise.addEventListener('click', () => {
        if (!hasData) return;
        
        showLoader();
        setStatus("Applying Noise...", "#fbbf24");
        const threshold = parseInt(noiseSlider.value, 10);
        
        fetch('/api/distort/noise', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ threshold })
        })
        .then(res => res.json())
        .then(data => {
            hideLoader();
            if (data.error) {
                alert("Error applying noise: " + data.error);
                setStatus("Error", "#ef4444");
                return;
            }
            handleStateUpdate(data.state);
            setStatus(`Noise Applied (Thresh: ${threshold})`, "#38bdf8");
        })
        .catch(err => {
            hideLoader();
            console.error(err);
            setStatus("Network Error", "#ef4444");
        });
    });

    document.addEventListener('keydown', (e) => {
        if (!hasData) return;
        
        // Prevent default scrolling for arrows
        if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
            e.preventDefault();
            
            const direction = e.key === 'ArrowLeft' ? 'left' : 'right';
            
            fetch('/api/action/move', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ direction })
            })
            .then(res => res.json())
            .then(data => {
                if (!data.error) {
                    handleStateUpdate(data.state);
                }
            })
            .catch(console.error);
        }
    });

    const handleStateUpdate = (state) => {
        hasData = state.has_data;
        fixCount.innerText = state.fixations.length || 0;
        
        if (state.fixations) {
            visualizer.setData(state.fixations, state.image_url);
        }
        updateControls();
    };
});
