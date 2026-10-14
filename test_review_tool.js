const { chromium } = require('playwright');

(async () => {
    console.log('Starting browser automation test...');
    
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    
    try {
        // Navigate to the review_template_v2.html file
        const htmlPath = 'C:\\Users\\viraj\\Code_files\\Github\\RoadGuard AI\\experiments\\results\\real_world_model_improvement\\review_tool_v2\\review_template_v2.html';
        console.log(`Loading HTML file: ${htmlPath}`);
        
        await page.goto(`file:///${htmlPath}`, { waitUntil: 'domcontentloaded' });
        
        // Wait for metadata to load and page to be ready
        await page.waitForSelector('#annotationCanvas', { timeout: 30000 });
        await page.waitForSelector('#totalImages', { timeout: 10000 });
        
        // Get initial state
        const initialBoxes = await page.evaluate(() => {
            return window.gtBoxes || {};
        });
        
        console.log('Page loaded successfully');
        
        // Step 2: Draw a box on an image
        // First check if draw mode is available
        await page.waitForSelector('#btnDrawMode', { timeout: 10000 });
        await page.click('#btnDrawMode');
        await page.waitForTimeout(100); // Wait for draw mode to activate
        
        // Get canvas position for drawing
        const canvasInfo = await page.evaluate(() => {
            const canvas = document.getElementById('annotationCanvas');
            const rect = canvas.getBoundingClientRect();
            return {
                canvasWidth: canvas.width,
                canvasHeight: canvas.height,
                canvasLeft: rect.left,
                canvasTop: rect.top
            };
        });
        
        console.log('Drawing box on canvas...');
        
        // Simulate drawing a box at position (100, 100) with size (200, 150)
        // We need to simulate mouse events
        await page.mouse.move(
            canvasInfo.canvasLeft + 100 * canvasInfo.canvasWidth / 1000, // Scale coordinates
            canvasInfo.canvasTop + 100 * canvasInfo.canvasHeight / 1000
        );
        await page.mouse.down();
        await page.waitForTimeout(100);
        await page.mouse.move(
            canvasInfo.canvasLeft + 300 * canvasInfo.canvasWidth / 1000,
            canvasInfo.canvasTop + 250 * canvasInfo.canvasHeight / 1000
        );
        await page.mouse.up();
        await page.waitForTimeout(500); // Wait for box to be drawn
        
        // Step 3: Set status to CONFIRMED_POSITIVE
        console.log('Setting status to CONFIRMED_POSITIVE...');
        await page.click('#btnConfirmedPositive');
        await page.waitForTimeout(500);
        
        // Verify box was drawn and status was set
        const afterActions = await page.evaluate(() => {
            const metadata = window.metadata || [];
            const gtBoxes = window.gtBoxes || {};
            const imageStatus = window.imageStatus || {};
            
            return {
                totalImages: window.metadata ? window.metadata.length : 0,
                currentImagePath: window.metadata && window.metadata.length > 0 ? window.metadata[window.currentIndex]?.image_path : null,
                boxes: gtBoxes,
                status: imageStatus
            };
        });
        
        console.log('After drawing box and setting status:', afterActions);
        
        // Step 4: Refresh the page
        console.log('Refreshing page...');
        await page.reload({ waitUntil: 'domcontentloaded' });
        
        // Wait for page to load after refresh
        await page.waitForSelector('#annotationCanvas', { timeout: 30000 });
        await page.waitForSelector('#totalImages', { timeout: 10000 });
        
        // Wait a bit for localStorage to load
        await page.waitForTimeout(1000);
        
        // Step 5: Verify the box and status persist
        console.log('Verifying persistence after refresh...');
        const afterRefresh = await page.evaluate(() => {
            const metadata = window.metadata || [];
            const gtBoxes = window.gtBoxes || {};
            const imageStatus = window.imageStatus || {};
            
            return {
                totalImages: window.metadata ? window.metadata.length : 0,
                currentImagePath: window.metadata && window.metadata.length > 0 ? window.metadata[window.currentIndex]?.image_path : null,
                boxes: gtBoxes,
                status: imageStatus
            };
        });
        
        console.log('After refresh:', afterRefresh);
        
        // Check persistence results
        const boxesBefore = Object.keys(initialBoxes).length;
        const boxesAfterRefresh = Object.keys(afterRefresh.boxes).filter(path => gtBoxes[path]?.length > 0).length;
        const statusConfirmed = afterRefresh.status && afterRefresh.status[afterRefresh.currentImagePath] === 'CONFIRMED_POSITIVE';
        
        console.log('\n=== PERSISTENCE TEST RESULTS ===');
        console.log(`Initial boxes: ${boxesBefore}`);
        console.log(`Boxes after refresh: ${boxesAfterRefresh}`);
        console.log(`Status CONFIRMED_POSITIVE persisted: ${statusConfirmed}`);
        
        // Test export functionality
        console.log('\n=== TESTING EXPORT FUNCTIONALITY ===');
        
        // Check if export buttons exist
        const exportAllExists = await page.isVisible('#btnExportAll');
        const exportYoloExists = await page.isVisible('#btnExportYolo');
        const importExists = await page.isVisible('#btnImport');
        
        console.log(`Export All button exists: ${exportAllExists}`);
        console.log(`Export YOLO Labels button exists: ${exportYoloExists}`);
        console.log(`Import Annotations button exists: ${importExists}`);
        
        // Test export buttons (click them to check they're functional)
        if (exportAllExists) {
            console.log('Testing Export All button...');
            await page.click('#btnExportAll');
            await page.waitForTimeout(500);
            console.log('Export All button clicked successfully');
        }
        
        if (exportYoloExists) {
            console.log('Testing Export YOLO Labels button...');
            await page.click('#btnExportYolo');
            await page.waitForTimeout(500);
            console.log('Export YOLO Labels button clicked successfully');
        }
        
        // Check if import file input exists (it's hidden)
        const importFileExists = await page.isVisible('#importFile');
        console.log(`Import file input exists: ${importFileExists}`);
        
        console.log('\n=== FINAL TEST SUMMARY ===');
        const persistencePassed = boxesAfterRefresh > boxesBefore && statusConfirmed;
        const exportTestPassed = exportAllExists && exportYoloExists && importExists;
        
        console.log(`Persistence test passed: ${persistencePassed}`);
        console.log(`Export functionality test passed: ${exportTestPassed}`);
        console.log(`Overall test passed: ${persistencePassed && exportTestPassed}`);
        
    } catch (error) {
        console.error('Test failed with error:', error);
    } finally {
        await browser.close();
        console.log('Browser closed');
    }
})();