window.addEventListener("load", () => {
    const track = document.querySelector('.carousel-track');
    const slides = Array.from(document.querySelectorAll('.carousel-slide'));
    const nextButton = document.querySelector('.next-btn');
    const prevButton = document.querySelector('.prev-btn');

    // Safety check: only run code if carousel elements exist on the page
    if (!track || slides.length === 0 || !nextButton || !prevButton) {
        return; 
    }

    let currentIndex = 0;

    // Calculates the precise current width of a slide and shifts the track
    function updateSlidePosition() {
        const slideWidth = slides[0].getBoundingClientRect().width;
        track.style.transform = `translateX(-${currentIndex * slideWidth}px)`;
    }

    // Next Button Click Actions
    nextButton.addEventListener('click', () => {
        if (currentIndex < slides.length - 1) {
            currentIndex++;
        } else {
            currentIndex = 0; // Loop back to the first slide
        }
        updateSlidePosition();
    });

    // Previous Button Click Actions
    prevButton.addEventListener('click', () => {
        if (currentIndex > 0) {
            currentIndex--;
        } else {
            currentIndex = slides.length - 1; // Wrap around to the last slide
        }
        updateSlidePosition();
    });

    // Recalculate dimensions cleanly if the window changes sizes
    window.addEventListener('resize', updateSlidePosition);
});