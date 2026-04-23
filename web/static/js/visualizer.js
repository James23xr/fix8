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
        
        // (Rendering logic to be implemented in PR 6)
    }
    
    _setupEvents() {
        // (Interactive tooltip logic to be implemented in PR 7)
    }
}
