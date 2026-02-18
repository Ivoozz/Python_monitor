// Dashboard JavaScript - Auto-refresh, Graphs, and Dark Mode

// Configuration
const POLL_INTERVAL = 5000; // 5 seconds
let refreshTimer = null;
let metricsHistory = {
    cpu: [],
    memory: [],
    load: [],
    disk: []
};
const MAX_HISTORY_POINTS = 20;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    loadDevices();
    refreshMetrics();
    startAutoRefresh();
    setupAddDeviceForm();
});

// Load devices list
async function loadDevices() {
    try {
        const response = await fetch('/api/devices');
        const data = await response.json();
        renderDevices(data.devices);
    } catch (error) {
        console.error('Error loading devices:', error);
    }
}

// Refresh metrics from all devices
async function refreshMetrics() {
    const lastUpdated = document.getElementById('last-updated');
    lastUpdated.textContent = 'Last updated: Loading...';
    
    try {
        const response = await fetch('/api/metrics');
        const data = await response.json();
        
        // Update last updated time
        const now = new Date();
        lastUpdated.textContent = `Last updated: ${now.toLocaleTimeString()}`;
        
        // Update summary cards
        updateSummary(data.summary);
        
        // Update devices display
        renderMetrics(data.devices);
        
        // Update graphs
        updateGraphs(data.devices);
        
    } catch (error) {
        console.error('Error refreshing metrics:', error);
        lastUpdated.textContent = 'Last updated: Error';
    }
}

// Start auto-refresh
function startAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
    refreshTimer = setInterval(refreshMetrics, POLL_INTERVAL);
    console.log(`Auto-refresh started (${POLL_INTERVAL}ms interval)`);
}

// Setup add device form
function setupAddDeviceForm() {
    const form = document.getElementById('add-device-form');
    const messageDiv = document.getElementById('form-message');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const name = document.getElementById('device-name').value.trim();
        const host = document.getElementById('device-host').value.trim();
        const port = document.getElementById('device-port').value;
        
        try {
            const response = await fetch('/api/devices', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ name, host, port })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                showMessage(data.message, 'success');
                form.reset();
                loadDevices();
                refreshMetrics();
            } else {
                showMessage(data.error || 'Failed to add device', 'error');
            }
        } catch (error) {
            console.error('Error adding device:', error);
            showMessage('Failed to add device', 'error');
        }
    });
}

// Show form message
function showMessage(message, type) {
    const messageDiv = document.getElementById('form-message');
    messageDiv.textContent = message;
    messageDiv.className = `form-message ${type}`;
    
    setTimeout(() => {
        messageDiv.className = 'form-message';
    }, 5000);
}

// Update summary cards
function updateSummary(summary) {
    document.getElementById('total-devices').textContent = summary.total || 0;
    document.getElementById('online-devices').textContent = summary.success || 0;
    document.getElementById('offline-devices').textContent = summary.error || 0;
    
    // Count alerts from all devices
    const totalAlerts = document.querySelectorAll('.alert-item').length;
    document.getElementById('total-alerts').textContent = totalAlerts;
}

// Render devices list
function renderDevices(devices) {
    const container = document.getElementById('devices-container');
    
    if (!devices || devices.length === 0) {
        container.innerHTML = `
            <div class="no-devices">
                <div class="no-devices-icon"><i class="fa-solid fa-server"></i></div>
                <h3>No devices configured</h3>
                <p>Add a device above to start monitoring</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = devices.map(device => `
        <div class="device-card" data-device-name="${device.name}">
            <div class="device-header">
                <span class="device-name">${device.name}</span>
                <span class="device-status ${device.enabled ? 'online' : 'disabled'}">
                    <i class="fa-solid ${device.enabled ? 'fa-check' : 'fa-ban'}"></i>
                    ${device.enabled ? 'Enabled' : 'Disabled'}
                </span>
            </div>
            <div class="device-info">
                <div class="device-info-item">
                    <span class="device-info-label"><i class="fa-solid fa-network-wired"></i> Host</span>
                    <span class="device-info-value">${device.host}:${device.port}</span>
                </div>
                <div class="device-info-item">
                    <span class="device-info-label"><i class="fa-regular fa-calendar"></i> Added</span>
                    <span class="device-info-value">${new Date(device.added_at).toLocaleDateString()}</span>
                </div>
            </div>
            <div class="device-actions">
                <button class="btn btn-secondary" onclick="toggleDevice('${device.name}', ${!device.enabled})">
                    <i class="fa-solid ${device.enabled ? 'fa-toggle-on' : 'fa-toggle-off'}"></i>
                    ${device.enabled ? 'Disable' : 'Enable'}
                </button>
                <button class="btn btn-danger" onclick="deleteDevice('${device.name}')">
                    <i class="fa-solid fa-trash"></i>
                    Remove
                </button>
            </div>
        </div>
    `).join('');
}

// Render metrics for each device
function renderMetrics(devices) {
    const container = document.getElementById('devices-container');
    
    if (!devices || devices.length === 0) {
        return;
    }
    
    container.innerHTML = devices.map(device => {
        const metrics = device;
        const statusClass = metrics.status === 'success' ? 'status-success' : 
                          metrics.status === 'disabled' ? 'status-disabled' : 'status-error';
        
        const statusLabel = metrics.status === 'success' ? 'Online' : 
                           metrics.status === 'disabled' ? 'Disabled' : 'Offline';
        
        // Build metrics HTML
        let metricsHtml = '';
        let alertsHtml = '';
        
        if (metrics.status === 'success') {
            metricsHtml = `
                <div class="device-metrics">
                    <div class="metric-item">
                        <div class="metric-value">${metrics.cpu_usage.toFixed(1)}%</div>
                        <div class="metric-label">CPU</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">${metrics.memory_usage.percent.toFixed(1)}%</div>
                        <div class="metric-label">Memory</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">${metrics.system_load['1min'].toFixed(2)}</div>
                        <div class="metric-label">Load (1m)</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">${metrics.disk_usage.percent.toFixed(1)}%</div>
                        <div class="metric-label">Disk</div>
                    </div>
                </div>
                <div class="device-metrics">
                    <div class="metric-item">
                        <div class="metric-value">${metrics.memory_usage.used.toFixed(1)} GB</div>
                        <div class="metric-label">Mem Used</div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-value">${metrics.disk_usage.used.toFixed(1)} GB</div>
                        <div class="metric-label">Disk Used</div>
                    </div>
                    ${metrics.cpu_temperature ? `
                    <div class="metric-item">
                        <div class="metric-value">${metrics.cpu_temperature.toFixed(1)}°C</div>
                        <div class="metric-label">Temp</div>
                    </div>
                    ` : ''}
                </div>
            `;
            
            // Alerts
            if (metrics.alerts && metrics.alerts.length > 0) {
                alertsHtml = `
                    <div class="device-alerts">
                        <h4><i class="fa-solid fa-triangle-exclamation"></i> Alerts (${metrics.alerts.length})</h4>
                        ${metrics.alerts.map(alert => `
                            <div class="alert-item"><i class="fa-solid fa-circle-exclamation"></i> ${alert.message}</div>
                        `).join('')}
                    </div>
                `;
            }
        } else {
            metricsHtml = `
                <div class="no-devices" style="padding: 20px;">
                    ${metrics.error || 'No data available'}
                </div>
            `;
        }
        
        return `
            <div class="device-card ${statusClass}">
                <div class="device-header">
                    <span class="device-name">${metrics.device_name || metrics.name}</span>
                    <span class="device-status ${statusClass === 'status-success' ? 'online' : statusClass === 'status-disabled' ? 'disabled' : 'offline'}">
                        ${statusLabel}
                    </span>
                </div>
                ${metricsHtml}
                ${alertsHtml}
            </div>
        `;
    }).join('');
}

// Update graphs
function updateGraphs(devices) {
    // Calculate averages across all online devices
    const onlineDevices = devices.filter(d => d.status === 'success');
    
    if (onlineDevices.length === 0) {
        return;
    }
    
    const now = new Date().toLocaleTimeString();
    
    // Calculate averages
    const avgCpu = onlineDevices.reduce((sum, d) => sum + d.cpu_usage, 0) / onlineDevices.length;
    const avgMemory = onlineDevices.reduce((sum, d) => sum + d.memory_usage.percent, 0) / onlineDevices.length;
    const avgLoad = onlineDevices.reduce((sum, d) => sum + d.system_load['1min'], 0) / onlineDevices.length;
    const avgDisk = onlineDevices.reduce((sum, d) => sum + d.disk_usage.percent, 0) / onlineDevices.length;
    
    // Add to history
    addHistoryPoint('cpu', now, avgCpu);
    addHistoryPoint('memory', now, avgMemory);
    addHistoryPoint('load', now, avgLoad);
    addHistoryPoint('disk', now, avgDisk);
    
    // Draw graphs
    drawGraph('cpu-graph', metricsHistory.cpu, '#667eea', '%');
    drawGraph('memory-graph', metricsHistory.memory, '#42a5f5', '%');
    drawGraph('load-graph', metricsHistory.load, '#ffa726', '');
    drawGraph('disk-graph', metricsHistory.disk, '#ab47bc', '%');
}

// Add history point
function addHistoryPoint(type, label, value) {
    metricsHistory[type].push({ label, value });
    if (metricsHistory[type].length > MAX_HISTORY_POINTS) {
        metricsHistory[type].shift();
    }
}

// Draw graph on canvas
function drawGraph(canvasId, data, color, unit) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !data || data.length === 0) {
        return;
    }
    
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    
    // Set canvas size
    canvas.width = rect.width * 2;
    canvas.height = rect.height * 2;
    ctx.scale(2, 2);
    
    const width = rect.width;
    const height = rect.height;
    const padding = { top: 20, right: 20, bottom: 30, left: 40 };
    const graphWidth = width - padding.left - padding.right;
    const graphHeight = height - padding.top - padding.bottom;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Theme-aware colors
    const isDarkMode = document.documentElement.classList.contains('theme-dark');
    const gridColor = isDarkMode ? '#334155' : '#e0e0e0';
    const textColor = isDarkMode ? '#cbd5e1' : '#666';
    
    // Find min/max values
    const values = data.map(d => d.value);
    const minValue = Math.min(...values) * 0.9;
    const maxValue = Math.max(...values) * 1.1;
    const valueRange = maxValue - minValue || 1;
    
    // Draw grid lines
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = 0; i <= 4; i++) {
        const y = padding.top + (graphHeight * i / 4);
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
    }
    ctx.stroke();
    
    // Draw data line
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    data.forEach((point, index) => {
        const x = padding.left + (index / (data.length - 1 || 1)) * graphWidth;
        const y = padding.top + graphHeight - ((point.value - minValue) / valueRange) * graphHeight;
        
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    ctx.stroke();
    
    // Draw area under line (with transparency)
    ctx.fillStyle = color + '20';
    ctx.lineTo(padding.left + graphWidth, padding.top + graphHeight);
    ctx.lineTo(padding.left, padding.top + graphHeight);
    ctx.closePath();
    ctx.fill();
    
    // Draw points
    ctx.fillStyle = color;
    data.forEach((point, index) => {
        const x = padding.left + (index / (data.length - 1 || 1)) * graphWidth;
        const y = padding.top + graphHeight - ((point.value - minValue) / valueRange) * graphHeight;
        
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fill();
    });
    
    // Draw y-axis labels
    ctx.fillStyle = textColor;
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'right';
    for (let i = 0; i <= 4; i++) {
        const value = maxValue - (valueRange * i / 4);
        const y = padding.top + (graphHeight * i / 4);
        ctx.fillText(value.toFixed(1) + unit, padding.left - 5, y + 3);
    }
    
    // Draw x-axis labels (show every 4th point)
    ctx.textAlign = 'center';
    data.forEach((point, index) => {
        if (index % 4 === 0 || index === data.length - 1) {
            const x = padding.left + (index / (data.length - 1 || 1)) * graphWidth;
            ctx.fillText(point.label, x, height - 10);
        }
    });
    
    // Draw current value
    const lastValue = data[data.length - 1].value;
    ctx.fillStyle = color;
    ctx.font = 'bold 14px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`${lastValue.toFixed(1)}${unit}`, padding.left, padding.top - 5);
}

// Toggle device enable/disable
async function toggleDevice(name, enabled) {
    try {
        const response = await fetch(`/api/devices/${encodeURIComponent(name)}/toggle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ enabled })
        });
        
        if (response.ok) {
            loadDevices();
            refreshMetrics();
        }
    } catch (error) {
        console.error('Error toggling device:', error);
    }
}

// Delete device
async function deleteDevice(name) {
    if (!confirm(`Are you sure you want to remove device "${name}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/devices/${encodeURIComponent(name)}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadDevices();
            refreshMetrics();
            showMessage(`Device "${name}" removed`, 'success');
        }
    } catch (error) {
        console.error('Error deleting device:', error);
        showMessage('Failed to remove device', 'error');
    }
}

// Handle window resize for canvas redraw
window.addEventListener('resize', function() {
    // Redraw graphs with new dimensions
    drawGraph('cpu-graph', metricsHistory.cpu, '#667eea', '%');
    drawGraph('memory-graph', metricsHistory.memory, '#42a5f5', '%');
    drawGraph('load-graph', metricsHistory.load, '#ffa726', '');
    drawGraph('disk-graph', metricsHistory.disk, '#ab47bc', '%');
});

// ========================================
// Theme Management (Dark Mode)
// ========================================

/**
 * Initialize theme based on saved preference or system preference
 */
function initTheme() {
    const savedTheme = localStorage.getItem('dashboard-theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    // Use saved theme, or fall back to system preference
    const prefersDark = savedTheme === 'dark' || (!savedTheme && systemPrefersDark);
    
    setTheme(prefersDark);
    
    // Listen for system preference changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        // Only auto-switch if user hasn't manually set a preference
        if (!localStorage.getItem('dashboard-theme')) {
            setTheme(e.matches);
        }
    });
    
    // Setup theme toggle button
    setupThemeToggle();
}

/**
 * Set the theme (dark or light)
 * @param {boolean} isDark - Whether to use dark mode
 */
function setTheme(isDark) {
    const htmlElement = document.documentElement;
    const bodyElement = document.body;
    const themeToggleBtn = document.getElementById('theme-toggle');
    
    if (isDark) {
        htmlElement.classList.add('theme-dark');
        bodyElement.classList.add('theme-dark');
        if (themeToggleBtn) {
            const icon = themeToggleBtn.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-moon');
                icon.classList.add('fa-sun');
            }
            themeToggleBtn.setAttribute('title', 'Switch to light mode');
            themeToggleBtn.setAttribute('aria-label', 'Switch to light mode');
        }
    } else {
        htmlElement.classList.remove('theme-dark');
        bodyElement.classList.remove('theme-dark');
        if (themeToggleBtn) {
            const icon = themeToggleBtn.querySelector('i');
            if (icon) {
                icon.classList.remove('fa-sun');
                icon.classList.add('fa-moon');
            }
            themeToggleBtn.setAttribute('title', 'Switch to dark mode');
            themeToggleBtn.setAttribute('aria-label', 'Switch to dark mode');
        }
    }
}

/**
 * Setup theme toggle button functionality
 */
function setupThemeToggle() {
    const themeToggleBtn = document.getElementById('theme-toggle');
    
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            const isDark = document.documentElement.classList.contains('theme-dark');
            const newTheme = isDark ? 'light' : 'dark';
            
            // Save user's preference
            localStorage.setItem('dashboard-theme', newTheme);
            
            // Apply the new theme
            setTheme(!isDark);
            
            // Optional: Add a small animation feedback
            themeToggleBtn.style.transform = 'scale(0.95)';
            setTimeout(() => {
                themeToggleBtn.style.transform = '';
            }, 100);
        });
    }
}

/**
 * Get the current theme (for graph color adjustments if needed)
 * @returns {string} - 'dark' or 'light'
 */
function getCurrentTheme() {
    return document.documentElement.classList.contains('theme-dark') ? 'dark' : 'light';
}
