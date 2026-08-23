// script.js

document.addEventListener('DOMContentLoaded', () => {
    // TOC collapsible sections (index.html)
    document.querySelectorAll('.story-heading').forEach(heading => {
        heading.addEventListener('click', function () {
            const partsList = this.nextElementSibling;
            const isActive = partsList.classList.contains('active');
            document.querySelectorAll('.parts-list').forEach(list => list.classList.remove('active'));
            document.querySelectorAll('.story-heading').forEach(h => h.classList.remove('active'));
            if (!isActive) { partsList.classList.add('active'); this.classList.add('active'); }
        });
    });

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
