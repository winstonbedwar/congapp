import { initializeApp } from "https://www.gstatic.com/firebasejs/10.5.0/firebase-app.js";
import { getDatabase, ref, push } from "https://www.gstatic.com/firebasejs/10.5.0/firebase-database.js";

const firebaseConfig = {
    apiKey: "AIzaSyCS07UgX2GnmuufEQET-RYOtm8i0XaZkWk",
    authDomain: "orwell-ea558.firebaseapp.com",
    databaseURL: "https://orwell-ea558-default-rtdb.firebaseio.com",
    projectId: "orwell-ea558",
    storageBucket: "orwell-ea558.firebasestorage.app",
    messagingSenderId: "301391502605",
    appId: "1:301391502605:web:67c58902e72044cd03a444"
};

const app = initializeApp(firebaseConfig);
const db = getDatabase(app);

let currentStep = 1;
const totalSteps = 4;
let uploadedFiles = [];

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

function handleFiles(files) {
    Array.from(files).forEach(file => {
        if (file.size <= 10 * 1024 * 1024) {
            uploadedFiles.push(file);
            addFileToList(file);
        } else {
            alert(`${file.name} is too large. Max size is 10MB.`);
        }
    });
}

function addFileToList(file) {
    const fileList = document.getElementById('fileList');
    if (!fileList) return;
    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.innerHTML = `
        <div class="file-icon">📄</div>
        <div class="file-info">
            <div class="file-name">${file.name}</div>
            <div class="file-size">${formatFileSize(file.size)}</div>
        </div>
        <button class="remove-file">×</button>
    `;
    fileItem.querySelector('.remove-file').addEventListener('click', () => {
        uploadedFiles = uploadedFiles.filter(f => f.name !== file.name);
        renderFileList();
    });
    fileList.appendChild(fileItem);
}

function renderFileList() {
    const fileList = document.getElementById('fileList');
    if (!fileList) return;
    fileList.innerHTML = '';
    uploadedFiles.forEach(file => addFileToList(file));
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function updateForm() {
    document.querySelectorAll('.form-step').forEach(step => {
        step.classList.remove('active');
    });
    const activeStep = document.querySelector(`.form-step[data-step="${currentStep}"]`);
    if (activeStep) activeStep.classList.add('active');

    document.querySelectorAll('.step').forEach((step, index) => {
        step.classList.remove('active', 'completed');
        if (index + 1 < currentStep) {
            step.classList.add('completed');
        } else if (index + 1 === currentStep) {
            step.classList.add('active');
        }
    });

    const progressLine = document.getElementById('progressLine');
    const stepsContainer = document.querySelector('.progress-steps');
    if (progressLine && stepsContainer) {
        const totalWidth = stepsContainer.offsetWidth - 72;
        const progressPercent = ((currentStep - 1) / (totalSteps - 1)) * 100;
        progressLine.style.width = (progressPercent / 100) * totalWidth + 'px';
    }

    if (currentStep === 4) updateReview();
}

function updateReview() {
    const reviewContent = document.getElementById('reviewContent');
    if (!reviewContent) return;
    const data = {
        'Username': document.getElementById('username')?.value,
        'Email': document.getElementById('email')?.value,
        'Age': document.getElementById('age')?.value,
        'Occupation': document.getElementById('occupation')?.value,
        'Income': document.getElementById('income')?.value,
        'Gender': document.getElementById('gender')?.value,
        'Ethnicity': document.getElementById('ethnicity')?.value,
    };

    let html = '';
    for (let [key, value] of Object.entries(data)) {
        if (value) {
            html += `
                <div class="review-card">
                    <label>${key}</label>
                    <div class="review-card-value">${value}</div>
                </div>
            `;
        }
    }
    reviewContent.innerHTML = html;
}

function nextStep() {
    if (currentStep < totalSteps) {
        currentStep++;
        updateForm();
    }
}

function prevStep() {
    if (currentStep > 1) {
        currentStep--;
        updateForm();
    }
}

async function submitForm() {
    currentStep = 5;
    updateForm();

    const name = document.getElementById('username')?.value || '';
    const password = document.getElementById('password')?.value || '';
    const age = document.getElementById('age')?.value || '';
    const occupation = document.getElementById('occupation')?.value || '';
    const income = document.getElementById('income')?.value || '';
    const gender = document.getElementById('gender')?.value || '';
    const ethnicity = document.getElementById('ethnicity')?.value || '';
    const active = true;

    const messageEl = document.getElementById('message');

    try {
        await push(ref(db, 'users'), {
            name,
            password,
            age,
            occupation,
            income,
            gender,
            ethnicity,
            active
        });

        if (messageEl) messageEl.innerHTML = `<p style=\"color: green;\">User registered successfully! Redirecting...</p>`;
        setTimeout(() => { window.location.href = 'index.html'; }, 3100);
    } catch (err) {
        console.error('Error writing to database:', err);
        if (messageEl) messageEl.innerHTML = `<p style=\"color: red;\">Failed to register user.</p>`;
    }
}

window.addEventListener('DOMContentLoaded', () => {
    $$('.btn-next').forEach(btn => {
        if (btn.classList.contains('btn-submit')) return;
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            nextStep();
        });
    });

    $$('.btn-prev').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            prevStep();
        });
    });

    const submitBtn = $('.btn-submit');
    if (submitBtn) submitBtn.addEventListener('click', (e) => { e.preventDefault(); submitForm(); });

    updateForm();
});