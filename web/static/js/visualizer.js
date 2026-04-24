class Fix8Visualizer {
    constructor() {
        this.img = document.getElementById('engine-render');
        this.grid = document.getElementById('interactive-grid');
        this.tooltip = document.getElementById('tooltip');
        
        this.fixations = [];
        this.hoveredIndex = -1;
        this.isDragging = false;
        this.draggedIndex = -1;
        this.onFixationUpdate = null;
        
        this._setupEvents();
    }
    
    setData(fixations, imageUrl) {
        this.fixations = fixations || [];
        this.fixations.forEach(f => {
            f.x_cord = Number(f.x_cord);
            f.y_cord = Number(f.y_cord);
            f.duration = Number(f.duration);
        });
        this.hoveredIndex = -1;
        this.draw();
    }
    
    draw() {
        if (this.fixations.length === 0) {
            this.img.src = '';
            // Or handle empty state
            return;
        }
        // Force backend regeneration of Matplotlib pipeline
        this.img.src = '/api/render?t=' + Date.now();
    }
    
    _setupEvents() {
        // We use naturalWidth/Height to inversely scale CSS bounding boxes back to matplotlib data bounds
        const getMousePos = (e) => {
            const rect = this.img.getBoundingClientRect();
            // Matplotlib guarantees the output PNG intrinsically aligns with the maximum original image domain,
            // EXCEPT if matplotlib natively applies paddings. We used pad_inches=0 and tight_layout on the backend.
            const nativeScaleX = (this.img.naturalWidth && rect.width) ? (this.img.naturalWidth / rect.width) : 1;
            const nativeScaleY = (this.img.naturalHeight && rect.height) ? (this.img.naturalHeight / rect.height) : 1;
            
            return {
                x: (e.clientX - rect.left) * nativeScaleX,
                y: (e.clientY - rect.top) * nativeScaleY,
                rawX: e.clientX,
                rawY: e.clientY
            };
        };

        this.grid.addEventListener('mousedown', (e) => {
            if (this.hoveredIndex !== -1) {
                this.isDragging = true;
                this.draggedIndex = this.hoveredIndex;
            }
        });

        this.grid.addEventListener('mousemove', (e) => {
            if (this.fixations.length === 0) return;
            const pos = getMousePos(e);
            
            // Handle Dragging
            if (this.isDragging && this.draggedIndex !== -1) {
                // Instantly update local dataset so it doesn't snap back on subsequent network hops
                this.fixations[this.draggedIndex].x_cord = pos.x;
                this.fixations[this.draggedIndex].y_cord = pos.y;
                
                // Hide tooltip while dragging
                this.tooltip.style.opacity = '0';
                this.grid.style.cursor = 'grabbing';
                // NOTE: We don't call this.draw() continuously during drag to prevent backend spam!
                // We let the drop event fire the SSR re-render.
                return;
            }
            
            // Handle Hovering via the invisible datagrid
            let foundIndex = -1;
            
            for (let i = this.fixations.length - 1; i >= 0; i--) {
                const f = this.fixations[i];
                
                // The scaled hover radius matching matplotlib visual scatter area roughly
                const radius = Math.min(Math.max(f.duration / 25, 6), 35);
                const hoverRadius = radius + 8; // Margin buffer
                
                const dx = pos.x - f.x_cord;
                const dy = pos.y - f.y_cord;
                
                if (dx*dx + dy*dy <= hoverRadius*hoverRadius) {
                    foundIndex = i;
                    break;
                }
            }
            
            if (foundIndex !== this.hoveredIndex) {
                this.hoveredIndex = foundIndex;
                
                if (foundIndex !== -1) {
                    this.grid.style.cursor = 'grab'; // Indicates draggable
                } else {
                    this.tooltip.style.opacity = '0';
                    this.grid.style.cursor = 'crosshair';
                }
            }
            
            // Update tooltip text and position if hovering
            if (this.hoveredIndex !== -1 && !this.isDragging) {
                const f = this.fixations[this.hoveredIndex];
                this.tooltip.style.opacity = '1';
                this.tooltip.style.left = (pos.rawX + 15) + 'px';
                this.tooltip.style.top = (pos.rawY + 15) + 'px';
                this.tooltip.innerHTML = `
                    <div style="font-weight: 800; margin-bottom:4px; color:var(--accent-primary)">Fixation ${this.hoveredIndex}</div>
                    <div>X: <span style="color:#e2e8f0">${f.x_cord.toFixed(1)}</span></div>
                    <div>Y: <span style="color:#e2e8f0">${f.y_cord.toFixed(1)}</span></div>
                    <div>Duration: <span style="color:#e2e8f0">${f.duration.toFixed(1)}ms</span></div>
                    <div style="font-size: 0.70rem; color: #a1a1aa; margin-top: 4px;">Click & Drag to reposition</div>
                `;
            }
        });
        
        this.grid.addEventListener('mouseup', (e) => {
            if (this.isDragging) {
                const f = this.fixations[this.draggedIndex];
                
                // Fire callback to save to backend
                if (this.onFixationUpdate) {
                    this.onFixationUpdate(this.draggedIndex, f.x_cord, f.y_cord);
                }
                
                this.isDragging = false;
                this.draggedIndex = -1;
                this.grid.style.cursor = 'grab';
                
                // Redraw from backend immediately after drop
                this.draw(); 
            }
        });
        
        this.grid.addEventListener('mouseleave', () => {
            if (this.isDragging) {
                // If mouse leaves during drag, commit the drop
                const f = this.fixations[this.draggedIndex];
                if (this.onFixationUpdate) {
                    this.onFixationUpdate(this.draggedIndex, f.x_cord, f.y_cord);
                }
                this.isDragging = false;
                this.draggedIndex = -1;
                this.draw();
            }
            
            if (this.hoveredIndex !== -1) {
                this.hoveredIndex = -1;
                this.tooltip.style.opacity = '0';
                this.grid.style.cursor = 'crosshair';
            }
        });
    }
}
