document.addEventListener('DOMContentLoaded', function() {
    // --- THEME MANAGEMENT ---
    const themeToggleBtn = document.getElementById('theme-toggle');
    
    function setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        if (themeToggleBtn) {
            const icon = themeToggleBtn.querySelector('i');
            if (icon) {
                if (theme === 'dark') {
                    icon.className = 'fas fa-sun';
                } else {
                    icon.className = 'fas fa-moon';
                }
            }
        }
    }
    
    const savedTheme = localStorage.getItem('theme');
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    const initialTheme = savedTheme || systemTheme;
    setTheme(initialTheme);
    
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            setTheme(newTheme);
            window.dispatchEvent(new Event('themeChanged'));
        });
    }

    // --- ACTIVE SIDEBAR LINK ---
    const currentPath = window.location.pathname;
    const menuItems = document.querySelectorAll('.menu-item');
    menuItems.forEach(item => {
        const link = item.querySelector('a');
        if (link) {
            const href = link.getAttribute('href');
            if (currentPath === href || (href !== '/' && currentPath.startsWith(href))) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        }
    });

    // --- STORY SLIDESHOW CONTROLLER ---
    const storyCard = document.getElementById('story-card');
    if (storyCard) {
        initializeStory();
    }
    
    // --- PREDICTOR CONTROLLER ---
    const predictorForm = document.getElementById('predictor-form');
    if (predictorForm) {
        initializePredictor();
    }
    
    // --- DATABASE SQL HELPERS ---
    const sqlHelpers = document.querySelectorAll('.sql-helper-btn');
    const sqlEditor = document.getElementById('sql-editor');
    if (sqlHelpers.length > 0 && sqlEditor) {
        sqlHelpers.forEach(btn => {
            btn.addEventListener('click', function() {
                const query = this.getAttribute('data-query');
                sqlEditor.value = query;
            });
        });
    }
});

// --- STORY FUNCTIONS (10 SCENES) ---
function initializeStory() {
    const slides = [
        {
            num: 1,
            subtitle: "Scene 1: Introduction",
            title: "Understanding CardioSync Platform",
            text: `<p>Cardiovascular diseases (CVDs) are the leading cause of death globally, taking an estimated 17.9 million lives each year. Over 4 out of 5 CVD deaths are due to heart attacks and strokes.</p>
                   <p>Early identification, monitoring, and clinical risk scoring are key. **CardioSync** is designed to parse patient bio-markers, clean the inputs, evaluate statistical trends, and render preventative predictions.</p>`,
            visual: `<div style="text-align:center; padding: 20px;">
                        <i class="fas fa-heartbeat" style="font-size: 74px; color: var(--danger); margin-bottom: 16px; animation: pulse 1.5s infinite;"></i>
                        <h4 style="font-size: 20px; color: var(--text-primary); font-weight:800;">17.9M Lives</h4>
                        <p style="color: var(--text-secondary); font-size:12px; margin-bottom:0;">Annual Global Mortality Rate from CVDs</p>
                     </div>`
        },
        {
            num: 2,
            subtitle: "Scene 2: Dataset Overview",
            title: "UCI Cleveland Clinical Database",
            text: `<p>Our database contains clinical patient records with 14 standard heart parameters (expanded to 16, including Smoking and BMI).</p>
                   <p>The dataset includes critical diagnostic anomalies (e.g. vessel narrowing, maximum heart rate capacities, blood sugar, resting chest pain brackets, and thalassemia types), providing a robust baseline for predictive models.</p>`,
            visual: `<div style="text-align:center; padding: 20px;">
                        <i class="fas fa-database" style="font-size: 64px; color: var(--primary); margin-bottom: 16px;"></i>
                        <h4 style="font-size: 20px; color: var(--text-primary); font-weight:800;">303 Records</h4>
                        <p style="color: var(--text-secondary); font-size:12px; margin-bottom:0;">Patient Sample Sizes & Mapped Features</p>
                     </div>`
        },
        {
            num: 3,
            subtitle: "Scene 3: Risk Factors",
            title: "Identifying Clinical Indicators",
            text: `<p>Clinical research highlights specific markers linked to cardiac risk. The presence of exercise-induced angina, maximum heart rate fatigue, and blockages identified by fluoroscopy are among the strongest variables.</p>
                   <p>Our pipeline inspects these features, sanitizing outliers and resolving empty cells to ensure maximum accuracy during prediction checks.</p>`,
            visual: `<div style="text-align:center; padding: 20px;">
                        <i class="fas fa-stethoscope" style="font-size: 64px; color: var(--info); margin-bottom: 16px;"></i>
                        <h4 style="font-size: 18px; color: var(--text-primary); font-weight:800;">Key Indicators</h4>
                        <p style="color: var(--text-secondary); font-size:11px; margin-bottom:0;">Vessel counts (CA) and Thalassemia (Thal) show strong statistical significance.</p>
                     </div>`
        },
        {
            num: 4,
            subtitle: "Scene 4: Age Analysis",
            title: "Age-Related Cardiac Vulnerability",
            text: `<p>Patient age shows significant correlations with cardiovascular deterioration. While the median age in our clinical group is **54 years**, the incidence of disease shifts significantly after age 50.</p>
                   <p>Vessel narrowing (coronary blockages) and hypertension markers typically compound over time, increasing overall vulnerability.</p>`,
            visual: `<div style="text-align:center; padding: 10px;">
                        <i class="fas fa-calendar-alt" style="font-size: 54px; color: var(--warning); margin-bottom: 12px;"></i>
                        <h4 style="font-size: 18px; color: var(--text-primary); font-weight:800;">Risk Shifts</h4>
                        <p style="color: var(--text-secondary); font-size:12px; margin-bottom:4px;">Under 40: Low Incidence (~26%)</p>
                        <p style="color: var(--text-secondary); font-size:12px; margin-bottom:0;">Over 50: High Incidence (~48%)</p>
                     </div>`
        },
        {
            num: 5,
            subtitle: "Scene 5: Gender Analysis",
            title: "Gender & Biological Discrepancies",
            text: `<p>Biological sex is a major demographic factor. In our study group, male patients represent **68%** of records and show higher overall disease rates than female patients.</p>
                   <p>This variance highlights the need to configure gender-specific weights in our Machine Learning classifier to avoid diagnostic bias.</p>`,
            visual: `<div style="display:flex; flex-direction:column; gap:12px; padding: 10px;">
                        <div>
                            <div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:3px; color:var(--text-secondary);">
                                <span>Male (68% of study)</span>
                                <strong>High Risk</strong>
                            </div>
                            <div style="height: 8px; background-color: var(--border-color); border-radius:4px; overflow:hidden;">
                                <div style="height:100%; width: 55%; background-color: var(--danger);"></div>
                            </div>
                        </div>
                        <div>
                            <div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:3px; color:var(--text-secondary);">
                                <span>Female (32% of study)</span>
                                <strong>Lower Risk</strong>
                            </div>
                            <div style="height: 8px; background-color: var(--border-color); border-radius:4px; overflow:hidden;">
                                <div style="height:100%; width: 25%; background-color: var(--success);"></div>
                            </div>
                        </div>
                     </div>`
        },
        {
            num: 6,
            subtitle: "Scene 6: Cholesterol",
            title: "Serum Cholesterol Accretion",
            text: `<p>Serum Cholesterol (` + "`" + `chol` + "`" + `) measures lipid concentrations in the bloodstream. Levels above **240 mg/dl** represent high cholesterol, leading to arterial plaque accumulation (atherosclerosis).</p>
                   <p>High cholesterol narrows blood vessels, forcing the heart to work harder and increasing the risk of cardiovascular events.</p>`,
            visual: `<div style="text-align:center; padding: 20px;">
                        <i class="fas fa-droplet" style="font-size: 54px; color: var(--danger); margin-bottom: 16px;"></i>
                        <h4 style="font-size: 18px; color: var(--text-primary); font-weight:800;">High: &gt;=240 mg/dl</h4>
                        <p style="color: var(--text-secondary); font-size:11px; margin-bottom:0;">Associated with arterial narrowing.</p>
                     </div>`
        },
        {
            num: 7,
            subtitle: "Scene 7: Blood Pressure",
            title: "Systolic Hypertensive Cardiac Strain",
            text: `<p>Resting Blood Pressure (` + "`" + `trestbps` + "`" + `) measures force on arterial walls. Readings over **140 mm Hg** (Stage 1 Hypertension) increase myocardial strain, which can lead to cardiac failure over time.</p>
                   <p>Elevated blood pressure damages blood vessels, compounding other risk factors like high cholesterol.</p>`,
            visual: `<div style="text-align:center; padding: 20px;">
                        <i class="fas fa-gauge-high" style="font-size: 54px; color: var(--primary); margin-bottom: 16px;"></i>
                        <h4 style="font-size: 18px; color: var(--text-primary); font-weight:800;">Stage 1: &gt;=140 mm Hg</h4>
                        <p style="color: var(--text-secondary); font-size:11px; margin-bottom:0;">Associated with vessel wall weakening.</p>
                     </div>`
        },
        {
            num: 8,
            subtitle: "Scene 8: Smoking",
            title: "Vascular Damage from Tobacco",
            text: `<p>Smoking introduces carbon monoxide and nicotine into the bloodstream, directly damaging arterial lining and accelerating plaque build-up.</p>
                   <p>Smokers in our study exhibit a higher rate of cardiovascular events compared to non-smokers, making smoking status a key parameter in our screening model.</p>`,
            visual: `<div style="text-align:center; padding: 20px;">
                        <i class="fas fa-smoking" style="font-size: 54px; color: var(--warning); margin-bottom: 16px;"></i>
                        <h4 style="font-size: 18px; color: var(--text-primary); font-weight:800;">Acutely High Risk</h4>
                        <p style="color: var(--text-secondary); font-size:11px; margin-bottom:0;">Smoking directly accelerates arterial plaque accumulation.</p>
                     </div>`
        },
        {
            num: 9,
            subtitle: "Scene 9: BMI",
            title: "Obesity & Metabolic Syndrome",
            text: `<p>Body Mass Index (BMI) measures body fat. BMIs above **30.0** (obese range) are strongly linked to metabolic syndrome, diabetes, and heart disease.</p>
                   <p>Higher body mass increases systemic vascular resistance, forcing the heart to exert more pressure with every beat.</p>`,
            visual: `<div style="text-align:center; padding: 20px;">
                        <i class="fas fa-weight-scale" style="font-size: 54px; color: var(--info); margin-bottom: 16px;"></i>
                        <h4 style="font-size: 18px; color: var(--text-primary); font-weight:800;">Obese: BMI &gt;= 30.0</h4>
                        <p style="color: var(--text-secondary); font-size:11px; margin-bottom:0;">Correlated with elevated cardiac workload.</p>
                     </div>`
        },
        {
            num: 10,
            subtitle: "Scene 10: Conclusion",
            title: "Preventative Screening Logic",
            text: `<p>Diagnosing heart disease requires looking at the full clinical picture. No single marker tells the whole story: a patient with normal cholesterol may still have blockages or high blood pressure.</p>
                   <p>By combining all 15 parameters into our **Logistic Regression** model, CardioSync provides a robust, multi-dimensional risk prediction to assist clinicians in early screening.</p>`,
            visual: `<div style="text-align:center; padding: 20px;">
                        <i class="fas fa-check-double" style="font-size: 54px; color: var(--success); margin-bottom: 16px;"></i>
                        <h4 style="font-size: 18px; color: var(--text-primary); font-weight:800;">Multi-Feature Models</h4>
                        <p style="color: var(--text-secondary); font-size:11px; margin-bottom:0;">Interactive screening maps all features simultaneously.</p>
                     </div>`
        }
    ];
    
    let currentSlide = 0;
    
    const subtitleEl = document.getElementById('story-subtitle');
    const titleEl = document.getElementById('story-title');
    const textEl = document.getElementById('story-text');
    const visualEl = document.getElementById('story-visual');
    const prevBtn = document.getElementById('story-prev');
    const nextBtn = document.getElementById('story-next');
    const dotsContainer = document.getElementById('story-dots');
    
    dotsContainer.innerHTML = '';
    slides.forEach((slide, idx) => {
        const dot = document.createElement('div');
        dot.className = `story-step-dot ${idx === 0 ? 'active' : ''}`;
        dot.addEventListener('click', () => {
            goToSlide(idx);
        });
        dotsContainer.appendChild(dot);
    });
    
    function updateSlide() {
        const slide = slides[currentSlide];
        
        subtitleEl.textContent = slide.subtitle;
        titleEl.textContent = slide.title;
        textEl.innerHTML = slide.text;
        visualEl.innerHTML = slide.visual;
        
        const dots = dotsContainer.querySelectorAll('.story-step-dot');
        dots.forEach((dot, idx) => {
            if (idx === currentSlide) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
        
        prevBtn.disabled = currentSlide === 0;
        nextBtn.disabled = currentSlide === slides.length - 1;
        
        if (currentSlide === slides.length - 1) {
            nextBtn.innerHTML = `Finish <i class="fas fa-check"></i>`;
        } else {
            nextBtn.innerHTML = `Next <i class="fas fa-arrow-right"></i>`;
        }
    }
    
    function goToSlide(idx) {
        currentSlide = idx;
        updateSlide();
    }
    
    prevBtn.addEventListener('click', () => {
        if (currentSlide > 0) {
            currentSlide--;
            updateSlide();
        }
    });
    
    nextBtn.addEventListener('click', () => {
        if (currentSlide < slides.length - 1) {
            currentSlide++;
            updateSlide();
        } else {
            window.location.href = '/predict';
        }
    });
    
    updateSlide();
}

// --- PREDICTOR FUNCTIONS ---
function initializePredictor() {
    const form = document.getElementById('predictor-form');
    const resultsContainer = document.getElementById('results-placeholder');
    const contentContainer = document.getElementById('results-content');
    
    const gaugeBar = document.getElementById('gauge-bar');
    const gaugeValue = document.getElementById('risk-value');
    const riskBadge = document.getElementById('risk-badge');
    const suggestionList = document.getElementById('suggestions-list');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        resultsContainer.style.display = 'none';
        
        let loader = document.getElementById('form-loader');
        if (!loader) {
            loader = document.createElement('div');
            loader.id = 'form-loader';
            loader.innerHTML = `<div class="glass-card" style="display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:400px; text-align:center;">
                                    <i class="fas fa-spinner fa-spin" style="font-size: 40px; color: var(--primary); margin-bottom: 16px;"></i>
                                    <p style="color: var(--text-secondary);">Analyzing Patient Bio-markers...</p>
                                 </div>`;
            form.parentNode.appendChild(loader);
        }
        loader.style.display = 'block';
        
        fetch('/predict', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            loader.style.display = 'none';
            if (data.success) {
                resultsContainer.style.display = 'block';
                contentContainer.style.display = 'flex';
                
                const percentage = data.risk_percentage;
                const classification = data.risk_classification;
                const suggestions = data.suggestions;
                
                const offset = 565 - (565 * (percentage / 100));
                
                let colorClass = 'low';
                let strokeColor = 'var(--success)';
                if (classification === 'High') {
                    colorClass = 'high';
                    strokeColor = 'var(--danger)';
                } else if (classification === 'Medium') {
                    colorClass = 'medium';
                    strokeColor = 'var(--warning)';
                }
                
                gaugeBar.style.stroke = strokeColor;
                gaugeBar.style.strokeDashoffset = offset;
                
                animateCount(gaugeValue, 0, percentage, 1500);
                
                riskBadge.className = `risk-badge ${colorClass}`;
                riskBadge.textContent = `${classification} Risk`;
                
                suggestionList.innerHTML = '';
                suggestions.forEach(s => {
                    const li = document.createElement('li');
                    li.innerHTML = `<i class="fas fa-chevron-right"></i> <span>${s}</span>`;
                    suggestionList.appendChild(li);
                });
                
                if (window.innerWidth < 1000) {
                    resultsContainer.scrollIntoView({ behavior: 'smooth' });
                }
            } else {
                alert("Error making prediction: " + data.error);
            }
        })
        .catch(err => {
            loader.style.display = 'none';
            alert("Connection error: " + err);
        });
    });
}

function animateCount(element, start, end, duration) {
    let startTime = null;
    
    function step(timestamp) {
        if (!startTime) startTime = timestamp;
        const progress = Math.min((timestamp - startTime) / duration, 1);
        const val = progress * (end - start) + start;
        element.textContent = val.toFixed(1) + '%';
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    }
    
    window.requestAnimationFrame(step);
}
