// script.js

document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('.grid-container');

    if (container) {
        container.addEventListener('click', function(e) {
            // Check if we clicked a segment (span)
            const clickedSegment = e.target.closest('.segment');
            
            if (clickedSegment) {
                // 1. Get the ID of the clicked segment
                const segmentId = clickedSegment.getAttribute('data-segment-id');
                
                // 2. Remove highlight from ALL segments in the document
                document.querySelectorAll('.segment').forEach(el => {
                    el.classList.remove('active-segment');
                });

                // 3. Highlight all segments matching this ID (English & Sanskrit)
                if (segmentId) {
                    const targets = document.querySelectorAll(`.segment[data-segment-id="${segmentId}"]`);
                    targets.forEach(el => {
                        el.classList.add('active-segment');
                    });
                }
            }
        });
    }
});
