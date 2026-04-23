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
        // (Interactive tooltip logic to be implemented in PR 7)
    }
}
