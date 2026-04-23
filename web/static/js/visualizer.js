class Fix8Visualizer {
    constructor(canvasId, tooltipId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.tooltip = document.getElementById(tooltipId);
        
        this.fixations = [];
        this.offsetX = 0;
        this.offsetY = 0;
        
        this.hoveredIndex = -1;
        
        this._setupEvents();
        this.draw(); // initialize empty state
    }
    
    setData(fixations) {
        this.fixations = fixations || [];
        this.hoveredIndex = -1;
        this._computeBounds();
        this.draw();
    }
    
    _computeBounds() {
        if (this.fixations.length === 0) return;
        
        let minX = Infinity, minY = Infinity;
        let maxX = -Infinity, maxY = -Infinity;
        
        this.fixations.forEach(f => {
            if (f.x_cord < minX) minX = f.x_cord;
            if (f.x_cord > maxX) maxX = f.x_cord;
            if (f.y_cord < minY) minY = f.y_cord;
            if (f.y_cord > maxY) maxY = f.y_cord;
        });
        
        // Add padding
        const padding = 150;
        const width = maxX - minX + (padding*2);
        const height = maxY - minY + (padding*2);
        
        this.canvas.width = Math.max(width, 800);
        this.canvas.height = Math.max(height, 600);
        
        // Center the visualization bounds inside the canvas
        this.offsetX = Math.max(padding, (this.canvas.width - (maxX - minX)) / 2) - minX;
        this.offsetY = Math.max(padding, (this.canvas.height - (maxY - minY)) / 2) - minY;
    }
    
    draw() {
        // clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        if (this.fixations.length === 0) {
            this.ctx.fillStyle = '#94a3b8';
            this.ctx.font = '20px Inter, sans-serif';
            this.ctx.textAlign = 'center';
            this.ctx.fillText("No Data Loaded", this.canvas.width/2, this.canvas.height/2);
            return;
        }
        
        // Draw saccades (lines connecting fixations)
        this.ctx.beginPath();
        this.ctx.strokeStyle = 'rgba(56, 189, 248, 0.5)'; // vibrant cyan
        this.ctx.lineWidth = 2;
        
        for (let i = 0; i < this.fixations.length; i++) {
            const px = this.fixations[i].x_cord + this.offsetX;
            const py = this.fixations[i].y_cord + this.offsetY;
            if (i === 0) {
                this.ctx.moveTo(px, py);
            } else {
                this.ctx.lineTo(px, py);
            }
        }
        this.ctx.stroke();

        // Draw fixations (circles)
        for (let i = 0; i < this.fixations.length; i++) {
            const f = this.fixations[i];
            const px = f.x_cord + this.offsetX;
            const py = f.y_cord + this.offsetY;
            
            // Normalize duration for radius (e.g. min 6px, max 35px)
            const radius = Math.min(Math.max(f.duration / 25, 6), 35);
            
            this.ctx.beginPath();
            this.ctx.arc(px, py, radius, 0, 2 * Math.PI, false);
            
            if (i === this.hoveredIndex) {
                 this.ctx.fillStyle = 'rgba(251, 191, 36, 0.9)'; // hover color (amber)
                 this.ctx.fill();
                 this.ctx.lineWidth = 3;
                 this.ctx.strokeStyle = '#f59e0b';
                 this.ctx.stroke();
                 
                 // Glow effect
                 this.ctx.shadowBlur = 15;
                 this.ctx.shadowColor = 'rgba(245, 158, 11, 0.6)';
                 this.ctx.stroke();
                 this.ctx.shadowBlur = 0; // reset
            } else {
                 this.ctx.fillStyle = 'rgba(239, 68, 68, 0.65)'; // normal color (red)
                 this.ctx.fill();
                 this.ctx.lineWidth = 1;
                 this.ctx.strokeStyle = 'rgba(220, 38, 38, 0.9)';
                 this.ctx.stroke();
                 
                 // index text inside big enough circles
                 if (radius > 12) {
                     this.ctx.fillStyle = '#fff';
                     this.ctx.font = '600 11px Inter, sans-serif';
                     this.ctx.textAlign = 'center';
                     this.ctx.textBaseline = 'middle';
                     this.ctx.fillText(i.toString(), px, py);
                 }
            }
        }
    }
    
    _setupEvents() {
        this.canvas.addEventListener('mousemove', (e) => {
            if (this.fixations.length === 0) return;
            
            // Map screen coordinates to canvas coordinate space
            const rect = this.canvas.getBoundingClientRect();
            const scaleX = this.canvas.width / rect.width;
            const scaleY = this.canvas.height / rect.height;
            
            const mouseX = (e.clientX - rect.left) * scaleX;
            const mouseY = (e.clientY - rect.top) * scaleY;
            
            let foundIndex = -1;
            
            // Reverse loop to pick the circle drawn last (on top)
            for (let i = this.fixations.length - 1; i >= 0; i--) {
                const f = this.fixations[i];
                const px = f.x_cord + this.offsetX;
                const py = f.y_cord + this.offsetY;
                const radius = Math.min(Math.max(f.duration / 25, 6), 35);
                
                const hoverRadius = radius + 4; // allow generous margin for easy hovering
                
                const dx = mouseX - px;
                const dy = mouseY - py;
                
                if (dx*dx + dy*dy <= hoverRadius*hoverRadius) {
                    foundIndex = i;
                    break;
                }
            }
            
            if (foundIndex !== this.hoveredIndex) {
                this.hoveredIndex = foundIndex;
                this.draw(); 
                
                if (foundIndex !== -1) {
                    const f = this.fixations[foundIndex];
                    this.tooltip.style.opacity = '1';
                    this.tooltip.innerHTML = `
                        <div style="font-weight: 800; margin-bottom:4px; color:var(--accent-primary)">Fixation ${foundIndex}</div>
                        <div>X: <span style="color:#e2e8f0">${f.x_cord.toFixed(1)}</span></div>
                        <div>Y: <span style="color:#e2e8f0">${f.y_cord.toFixed(1)}</span></div>
                        <div>Duration: <span style="color:#e2e8f0">${f.duration.toFixed(1)}ms</span></div>
                    `;
                    this.canvas.style.cursor = 'pointer';
                } else {
                    this.tooltip.style.opacity = '0';
                    this.canvas.style.cursor = 'crosshair';
                }
            }
            
            // Move tooltip with mouse if visible
            if (this.hoveredIndex !== -1) {
                this.tooltip.style.left = (e.clientX + 15) + 'px';
                this.tooltip.style.top = (e.clientY + 15) + 'px';
            }
        });
        
        this.canvas.addEventListener('mouseleave', () => {
            if (this.hoveredIndex !== -1) {
                this.hoveredIndex = -1;
                this.tooltip.style.opacity = '0';
                this.canvas.style.cursor = 'crosshair';
                this.draw();
            }
        });
    }
}
