/**
 * Smart Academic Performance & Report Studio - Core App Controller
 * With exact 15-row per page split, College Logo, and clean downloads
 */

const state = {
  currentTab: 'upload',
  activeReportTab: 'advanced',
  filename: '',
  sheetNames: [],
  currentSheet: '',
  metadata: {
    institution: 'LORDS INSTITUTE OF ENGINEERING AND TECHNOLOGY',
    department: 'Department of Computer Science and Engineering',
    academic_year: '2024-25',
    course_name: 'PYTHON PROGRAMING',
    course_code: 'U23CM301',
    class_sec: 'II/C',
    semester: 'III',
    year_sem_sec: 'Class: II/C    Semester: III',
    faculty_name: 'Faculty Incharge'
  },
  allStudents: [],
  classified: {
    all_students: [],
    advanced_learners: [],
    average_learners: [],
    slow_learners: [],
    statistics: {}
  },
  thresholds: {
    advanced_cgpa_min: 7.5,
    advanced_cie_min: 15.0,
    slow_cgpa_max: 6.0,
    slow_cie_max: 10.0,
    slow_allow_backlogs: true
  },
  tableFilter: 'all',
  searchQuery: ''
};

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initUploadHandlers();
  initThresholdControls();
  initTableControls();
  initReportControls();
  
  const resetBtn = document.getElementById('resetSessionBtn');
  if (resetBtn) {
    resetBtn.addEventListener('click', resetSession);
  }

  // Start in empty state ready for user's CSV files
  switchTab('upload');
});

async function resetSession() {
  try {
    await fetch('/api/reset', { method: 'POST' });
    state.filename = '';
    state.sheetNames = [];
    state.currentSheet = '';
    state.allStudents = [];
    state.classified = { all_students: [], advanced_learners: [], average_learners: [], slow_learners: [], statistics: {} };
    
    const tray = document.getElementById('uploadedFilesTray');
    if (tray) tray.style.display = 'none';
    
    const sheetContainer = document.getElementById('sheetSelectContainer');
    if (sheetContainer) sheetContainer.style.display = 'none';

    renderStudentTable();
    updateDashboardView();
    updateReportPreview();
    switchTab('upload');
    showToast('Session reset. Ready for new files!', 'info');
  } catch (err) {
    console.error('Reset error:', err);
  }
}


function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.style.cssText = `
    position: fixed;
    bottom: 24px;
    right: 24px;
    background: ${type === 'error' ? '#f43f5e' : (type === 'success' ? '#10b981' : '#6366f1')};
    color: #fff;
    padding: 12px 20px;
    border-radius: 10px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.4);
    font-size: 0.875rem;
    font-weight: 500;
    z-index: 9999;
    display: flex;
    align-items: center;
    gap: 8px;
    animation: toastIn 0.3s ease;
  `;
  toast.innerHTML = `<span>${message}</span>`;
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3200);
}

function initNavigation() {
  document.querySelectorAll('.nav-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      switchTab(btn.dataset.tab);
    });
  });
}

function switchTab(tabId) {
  state.currentTab = tabId;
  document.querySelectorAll('.nav-tab').forEach(b => {
    b.classList.toggle('active', b.dataset.tab === tabId);
  });
  document.querySelectorAll('.tab-pane').forEach(p => {
    p.classList.toggle('active', p.id === `tab-${tabId}`);
  });

  if (tabId === 'dashboard') {
    updateDashboardView();
  } else if (tabId === 'editor') {
    renderStudentTable();
  } else if (tabId === 'reports') {
    updateReportPreview();
  }
}

async function fetchSamplesList() {
  try {
    const res = await fetch('/api/samples');
    const data = await res.json();
    const container = document.getElementById('samplesContainer');
    if (!container) return;

    container.innerHTML = '';
    data.samples.forEach(s => {
      const btn = document.createElement('button');
      btn.className = 'btn btn-secondary';
      btn.style.fontSize = '0.8rem';
      btn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        Load ${s.name}
      `;
      btn.onclick = () => loadSampleFile(s.name);
      container.appendChild(btn);
    });
  } catch (err) {
    console.error("Failed to load samples list", err);
  }
}

async function loadSampleFile(filename) {
  showToast(`Loading ${filename}...`, 'info');
  const formData = new FormData();
  formData.append('filename', filename);

  try {
    const res = await fetch('/api/load-sample', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.status === 'success') {
      applyLoadedData(data);
      showToast(`Loaded ${filename} (${data.summary.total_students} records)!`, 'success');
    }
  } catch (err) {
    console.error(err);
  }
}

function initUploadHandlers() {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('fileInput');

  if (dropzone && fileInput) {
    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
      dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files.length) {
        uploadMultipleFiles(e.dataTransfer.files);
      }
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length) {
        uploadMultipleFiles(e.target.files);
      }
    });
  }

  const sheetSelect = document.getElementById('sheetSelect');
  if (sheetSelect) {
    sheetSelect.addEventListener('change', async (e) => {
      const selectedSheet = e.target.value;
      if (!selectedSheet) return;
      showToast(`Loading sheet: ${selectedSheet}...`, 'info');
      const formData = new FormData();
      formData.append('sheet_name', selectedSheet);
      try {
        const res = await fetch('/api/change-sheet', {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        if (data.status === 'success') {
          applyLoadedData(data);
          showToast(`Sheet ${selectedSheet} loaded!`, 'success');
        }
      } catch (err) {
        showToast('Error switching sheet: ' + err.message, 'error');
      }
    });
  }
}

async function uploadMultipleFiles(files) {
  if (!files || !files.length) return;
  
  showToast(`Uploading & merging ${files.length} file(s)...`, 'info');
  const formData = new FormData();
  for (let i = 0; i < files.length; i++) {
    formData.append('files', files[i]);
  }

  try {
    const res = await fetch('/api/upload-multiple', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (data.status === 'success') {
      applyLoadedData(data);
      renderUploadedFilesTray(data.uploaded_files);
      showToast(`Successfully merged ${data.total_merged_students} students across ${files.length} file(s)!`, 'success');
      switchTab('reports');
    } else {
      throw new Error(data.detail || 'Upload failed');
    }
  } catch (err) {
    showToast('Upload error: ' + err.message, 'error');
  }
}

function renderUploadedFilesTray(filesList) {
  const tray = document.getElementById('uploadedFilesTray');
  if (!tray) return;
  if (!filesList || !filesList.length) {
    tray.style.display = 'none';
    return;
  }
  tray.style.display = 'flex';
  tray.innerHTML = filesList.map(f => `
    <div class="file-badge">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
      <span>${f.filename} (${f.sheet})</span>
      <span class="file-count">${f.records} stds</span>
    </div>
  `).join('');
}

function applyLoadedData(data) {
  state.filename = data.file_info ? data.file_info.filename : state.filename;
  state.sheetNames = data.file_info ? data.file_info.sheet_names : state.sheetNames;
  state.currentSheet = data.current_sheet;
  state.metadata = { ...state.metadata, ...data.metadata };
  state.classified = data.classified;
  state.allStudents = data.classified.all_students || [];

  const sheetContainer = document.getElementById('sheetSelectContainer');
  const sheetSelect = document.getElementById('sheetSelect');
  if (sheetSelect && state.sheetNames && state.sheetNames.length > 1) {
    sheetContainer.style.display = 'block';
    sheetSelect.innerHTML = state.sheetNames.map(s => 
      `<option value="${s}" ${s === state.currentSheet ? 'selected' : ''}>Subject Sheet: ${s}</option>`
    ).join('');
  } else if (sheetContainer) {
    sheetContainer.style.display = 'none';
  }

  syncMetadataInputs();
  updateDashboardView();
  renderStudentTable();
  updateReportPreview();
}

function syncMetadataInputs() {
  document.getElementById('metaInstitution').value = state.metadata.institution || '';
  document.getElementById('metaDepartment').value = state.metadata.department || '';
  document.getElementById('metaAcademicYear').value = state.metadata.academic_year || '';
  document.getElementById('metaCourseName').value = state.metadata.course_name || '';
  document.getElementById('metaClassSec').value = state.metadata.class_sec || 'II/C';
  document.getElementById('metaSemester').value = state.metadata.semester || 'III';
  document.getElementById('metaFacultyName').value = state.metadata.faculty_name || '';
}

function updateMetadataFromInputs() {
  state.metadata.institution = document.getElementById('metaInstitution').value;
  state.metadata.department = document.getElementById('metaDepartment').value;
  state.metadata.academic_year = document.getElementById('metaAcademicYear').value;
  state.metadata.course_name = document.getElementById('metaCourseName').value;
  state.metadata.class_sec = document.getElementById('metaClassSec').value;
  state.metadata.semester = document.getElementById('metaSemester').value;
  state.metadata.faculty_name = document.getElementById('metaFacultyName').value;
  updateReportPreview();
}

function initThresholdControls() {
  const advCgpaInput = document.getElementById('advCgpaInput');
  const advCieInput = document.getElementById('advCieInput');
  const slowCgpaInput = document.getElementById('slowCgpaInput');
  const slowCieInput = document.getElementById('slowCieInput');
  const applyBtn = document.getElementById('applyThresholdsBtn');

  if (applyBtn) {
    applyBtn.addEventListener('click', () => {
      state.thresholds.advanced_cgpa_min = parseFloat(advCgpaInput.value) || 7.5;
      state.thresholds.advanced_cie_min = parseFloat(advCieInput.value) || 15.0;
      state.thresholds.slow_cgpa_max = parseFloat(slowCgpaInput.value) || 6.0;
      state.thresholds.slow_cie_max = parseFloat(slowCieInput.value) || 10.0;

      reclassifyData();
      showToast('Thresholds updated & students re-categorized!', 'success');
    });
  }
}

async function reclassifyData() {
  try {
    const res = await fetch('/api/classify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        students: state.allStudents,
        thresholds: state.thresholds
      })
    });
    const data = await res.json();
    if (data.status === 'success') {
      state.classified = data.classified;
      state.allStudents = data.classified.all_students;
      updateDashboardView();
      renderStudentTable();
      updateReportPreview();
    }
  } catch (err) {
    console.error("Reclassification error", err);
  }
}

function updateDashboardView() {
  const stats = state.classified.statistics || {};
  document.getElementById('metricTotalStudents').innerText = stats.total_count || 0;
  document.getElementById('metricAdvCount').innerText = `${stats.advanced_count || 0} (${stats.advanced_percentage || 0}%)`;
  document.getElementById('metricAvgCount').innerText = `${stats.average_count || 0} (${stats.average_percentage || 0}%)`;
  document.getElementById('metricSlowCount').innerText = `${stats.slow_count || 0} (${stats.slow_percentage || 0}%)`;

  renderAnalyticsCharts(stats, state.allStudents);

  const topList = document.getElementById('topPerformersList');
  if (topList) {
    const adv = state.classified.advanced_learners || [];
    topList.innerHTML = adv.slice(0, 6).map((s, idx) => `
      <div style="display:flex; justify-content:space-between; align-items:center; padding: 10px 0; border-bottom: 1px solid rgba(148,163,184,0.1);">
        <div style="display:flex; align-items:center; gap:10px;">
          <span style="width:24px; height:24px; border-radius:50%; background:rgba(16,185,129,0.2); color:#10b981; display:flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:bold;">${idx+1}</span>
          <div>
            <div style="font-weight:600; font-size:0.875rem;">${s.student_name}</div>
            <div style="font-size:0.75rem; color:var(--text-muted);">${s.roll_number}</div>
          </div>
        </div>
        <div style="text-align:right;">
          <span class="badge-tier badge-advanced">${s.cgpa ? `CGPA ${s.cgpa}` : `CIE ${s.cie_marks}`}</span>
        </div>
      </div>
    `).join('') || '<div style="color:var(--text-muted); font-size:0.85rem;">No data available</div>';
  }

  const slowFocusList = document.getElementById('slowFocusList');
  if (slowFocusList) {
    const slow = state.classified.slow_learners || [];
    slowFocusList.innerHTML = slow.slice(0, 6).map((s, idx) => `
      <div style="display:flex; justify-content:space-between; align-items:center; padding: 10px 0; border-bottom: 1px solid rgba(148,163,184,0.1);">
        <div style="display:flex; align-items:center; gap:10px;">
          <span style="width:24px; height:24px; border-radius:50%; background:rgba(244,63,94,0.2); color:#f43f5e; display:flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:bold;">!</span>
          <div>
            <div style="font-weight:600; font-size:0.875rem;">${s.student_name}</div>
            <div style="font-size:0.75rem; color:var(--text-muted);">${s.roll_number} ${s.backlog_count > 0 ? `• <span style="color:#f43f5e;">${s.backlog_count} Backlog(s)</span>` : ''}</div>
          </div>
        </div>
        <div style="text-align:right;">
          <span class="badge-tier badge-slow">${s.cie_marks !== null && s.cie_marks !== undefined ? `CIE ${s.cie_marks}` : (s.cgpa ? `CGPA ${s.cgpa}` : 'Remedial')}</span>
        </div>
      </div>
    `).join('') || '<div style="color:var(--text-muted); font-size:0.85rem;">No slow learners identified</div>';
  }
}

function initTableControls() {
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('btn-primary'));
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.add('btn-secondary'));
      btn.classList.remove('btn-secondary');
      btn.classList.add('btn-primary');
      state.tableFilter = btn.dataset.filter;
      renderStudentTable();
    });
  });

  const searchInput = document.getElementById('tableSearchInput');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      state.searchQuery = e.target.value.toLowerCase();
      renderStudentTable();
    });
  }

  const addBtn = document.getElementById('addNewStudentBtn');
  if (addBtn) {
    addBtn.addEventListener('click', () => {
      const newRoll = prompt("Enter Student Roll / Hall Ticket Number:", `160923733${state.allStudents.length + 1}`);
      if (!newRoll) return;
      const newName = prompt("Enter Student Name:", "NEW STUDENT");
      if (!newName) return;

      const newStudent = {
        s_no: state.allStudents.length + 1,
        roll_number: newRoll,
        student_name: newName,
        cie_marks: 18.0,
        cgpa: 8.5,
        sgpa: 8.5,
        backlog_count: 0,
        observation_remarks: "Attentive & quick learner",
        action_plan: "Special project mentoring"
      };

      state.allStudents.unshift(newStudent);
      reclassifyData();
      showToast(`Added ${newName}!`, 'success');
    });
  }

  const batchBtn = document.getElementById('batchAssignBtn');
  if (batchBtn) {
    batchBtn.addEventListener('click', () => {
      state.allStudents.forEach(s => {
        if (s.tier === 'Slow') {
          s.action_plan = 'Remedial coaching, question bank assignments, and weekly progress tracking';
          s.observation_remarks = 'Needs conceptual reinforcement in core topics';
        } else if (s.tier === 'Advanced') {
          s.action_plan = 'Competitive coding, NPTEL certification, and research project presentation';
          s.observation_remarks = 'Exceptional problem solver with active participation';
        } else {
          s.action_plan = 'Weekly tutorial assignments and peer study group practice';
          s.observation_remarks = 'Consistent progress and regular attendance';
        }
      });
      renderStudentTable();
      updateReportPreview();
      showToast('Standardized action plans assigned to all students!', 'success');
    });
  }
}

function renderStudentTable() {
  const tbody = document.getElementById('studentTableBody');
  if (!tbody) return;

  let filtered = state.allStudents.filter(s => {
    if (state.tableFilter === 'advanced' && s.tier !== 'Advanced') return false;
    if (state.tableFilter === 'average' && s.tier !== 'Average') return false;
    if (state.tableFilter === 'slow' && s.tier !== 'Slow') return false;
    if (state.tableFilter === 'backlogs' && s.backlog_count === 0) return false;

    if (state.searchQuery) {
      const matchRoll = s.roll_number && s.roll_number.toLowerCase().includes(state.searchQuery);
      const matchName = s.student_name && s.student_name.toLowerCase().includes(state.searchQuery);
      if (!matchRoll && !matchName) return false;
    }
    return true;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding: 2rem; color:var(--text-muted);">No student records match your filter criteria</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map((s, idx) => {
    const origIdx = state.allStudents.indexOf(s);
    return `
      <tr>
        <td style="color:var(--text-dim); text-align:center;">${idx + 1}</td>
        <td>
          <input type="text" class="editable-cell" value="${s.roll_number || ''}" onchange="updateStudentField(${origIdx}, 'roll_number', this.value)" />
        </td>
        <td>
          <input type="text" class="editable-cell" style="font-weight:600;" value="${s.student_name || ''}" onchange="updateStudentField(${origIdx}, 'student_name', this.value)" />
        </td>
        <td>
          <input type="number" step="0.5" class="editable-cell" style="width:70px; text-align:center;" value="${s.cie_marks !== null && s.cie_marks !== undefined ? s.cie_marks : ''}" placeholder="-" onchange="updateStudentField(${origIdx}, 'cie_marks', parseFloat(this.value))" />
        </td>
        <td>
          <input type="number" step="0.01" class="editable-cell" style="width:70px; text-align:center;" value="${s.cgpa !== null && s.cgpa !== undefined ? s.cgpa : ''}" placeholder="-" onchange="updateStudentField(${origIdx}, 'cgpa', parseFloat(this.value))" />
        </td>
        <td>
          <select class="select-control" style="padding:4px 8px; font-size:0.75rem;" onchange="updateStudentTier(${origIdx}, this.value)">
            <option value="Advanced" ${s.tier === 'Advanced' ? 'selected' : ''}>🌟 Advanced</option>
            <option value="Average" ${s.tier === 'Average' ? 'selected' : ''}>🔹 Average</option>
            <option value="Slow" ${s.tier === 'Slow' ? 'selected' : ''}>⚠️ Slow</option>
          </select>
        </td>
        <td>
          <input type="text" class="editable-cell" value="${s.observation_remarks || ''}" placeholder="Add remarks..." onchange="updateStudentField(${origIdx}, 'observation_remarks', this.value)" />
        </td>
        <td>
          <input type="text" class="editable-cell" value="${s.action_plan || ''}" placeholder="Add intervention..." onchange="updateStudentField(${origIdx}, 'action_plan', this.value)" />
        </td>
        <td style="text-align:center;">
          <button class="btn btn-danger btn-sm" onclick="deleteStudent(${origIdx})" title="Delete student">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

function updateStudentField(studentIdx, field, value) {
  if (state.allStudents[studentIdx]) {
    state.allStudents[studentIdx][field] = value;
    updateReportPreview();
  }
}

function updateStudentTier(studentIdx, newTier) {
  if (state.allStudents[studentIdx]) {
    state.allStudents[studentIdx].tier = newTier;
    state.allStudents[studentIdx].category_override = newTier;
    reclassifyData();
  }
}

function deleteStudent(studentIdx) {
  if (confirm(`Remove ${state.allStudents[studentIdx].student_name}?`)) {
    state.allStudents.splice(studentIdx, 1);
    reclassifyData();
    showToast('Student removed', 'info');
  }
}

function initReportControls() {
  document.querySelectorAll('.report-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.report-tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.activeReportTab = btn.dataset.report;
      updateReportPreview();
    });
  });

  ['metaInstitution', 'metaDepartment', 'metaAcademicYear', 'metaCourseName', 'metaClassSec', 'metaSemester', 'metaFacultyName'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', updateMetadataFromInputs);
  });

  document.getElementById('downloadPdfBtn').addEventListener('click', () => downloadDocument('pdf'));
  document.getElementById('downloadDocxBtn').addEventListener('click', () => downloadDocument('docx'));
  document.getElementById('exportExcelBtn').addEventListener('click', exportToExcel);
  document.getElementById('printReportBtn').addEventListener('click', () => window.print());
}

function getTop15(students, sortKey, reverse) {
  let list = [...students];
  if (sortKey === 'cgpa') {
    list.sort((a, b) => ((b.cgpa || b.sgpa || 0) - (a.cgpa || a.sgpa || 0)));
  } else if (sortKey === 'slow_cgpa') {
    const failGroup = list.filter(s => s.backlog_count > 0 || (s.cgpa === null && s.sgpa === null));
    failGroup.sort((a, b) => (b.backlog_count || 0) - (a.backlog_count || 0));
    
    const passGroup = list.filter(s => (s.backlog_count === 0 || !s.backlog_count) && (s.cgpa !== null || s.sgpa !== null));
    passGroup.sort((a, b) => ((a.cgpa || a.sgpa || 99) - (b.cgpa || b.sgpa || 99)));
    
    list = [...failGroup, ...passGroup];
  } else if (sortKey === 'cie') {
    list.sort((a, b) => ((b.cie_marks || 0) - (a.cie_marks || 0)));
  } else if (sortKey === 'slow_cie') {
    list.sort((a, b) => ((a.cie_marks || 0) - (b.cie_marks || 0)));
  }
  return list.slice(0, 15);
}

function updateReportPreview() {
  const container = document.getElementById('reportPaperPreview');
  if (!container) return;

  if (!state.allStudents || state.allStudents.length === 0) {
    container.innerHTML = `
      <div class="glass-card" style="text-align:center; padding: 4.5rem 2rem; max-width: 650px; margin: 2rem auto;">
        <div style="width: 64px; height: 64px; border-radius: 50%; background: rgba(99,102,241,0.15); display: flex; align-items: center; justify-content: center; margin: 0 auto 1.5rem; color: var(--primary);">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
        </div>
        <h3 style="font-size: 1.3rem; font-weight: 700; margin-bottom: 8px;">No Marksheet / CSV Uploaded Yet</h3>
        <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1.5rem;">Please upload your marksheet or CSV file(s) in the <b>Upload & Parse</b> tab to preview and export the official 15-list reports.</p>
        <button class="btn btn-primary" onclick="switchTab('upload')">Go to Upload & Parse</button>
      </div>
    `;
    return;
  }

  const isAdv = (state.activeReportTab === 'advanced');
  const isSlow = (state.activeReportTab === 'slow');
  const isComp = (state.activeReportTab === 'comprehensive');

  const meta = state.metadata;
  const targetStudents = isAdv ? (state.classified.advanced_learners || []) : (isSlow ? (state.classified.slow_learners || []) : state.allStudents);
  const tierTitle = isAdv ? "Advance Learners List" : "Slow Learners List";

  const buildHeaderHtml = (subTitle, showSubject = true) => `
    <div class="page-header-wrap">
      <img src="/static/images/college_logo.png" class="college-logo-img" alt="Lords Logo" onerror="this.src='/static/images/college_logo.jpeg'" />
      <div class="college-text-block">
        <h2>${meta.institution || 'LORDS INSTITUTE OF ENGINEERING AND TECHNOLOGY'}</h2>
        <p>(UGC Autonomous Institution)</p>
        <p>Approved by AICTE | Affiliated to Osmania University | Estd.2003 | Accredited ‘A’ grade by NAAC</p>
        <div class="dept-text">${meta.department || 'Department of Computer Science and Engineering'}</div>
      </div>
    </div>

    <div class="header-divider-line"></div>

    <div class="page-center-info">
      <div class="center-ay">AY: ${meta.academic_year || '2024-25'}</div>
      ${showSubject ? `<div class="center-subject">Subject: ${meta.course_name || 'PYTHON PROGRAMING'}</div>` : ''}
      <div class="center-title"><b>${subTitle}</b></div>
    </div>

    <div class="page-meta-split-row">
      <div>Class: ${meta.class_sec || 'II/A'}</div>
      <div>Semester: ${meta.semester || 'III'}</div>
    </div>
  `;

  if (isAdv || isSlow) {
    const p1List = getTop15(targetStudents, isAdv ? 'cgpa' : 'slow_cgpa', isAdv);
    const p2List = isAdv ? getTop15(targetStudents, 'cgpa', true) : getTop15(targetStudents, 'slow_cgpa', false);
    const p3List = getTop15(targetStudents, isAdv ? 'cie' : 'slow_cie', isAdv);

    let html = `<div class="pages-container">`;

    // ===== PAGE 1: Previous Semester Result =====
    html += `
      <div class="paper-page">
        <div>
          ${buildHeaderHtml(`${tierTitle} – Based on the Previous Semester Result`, false)}
          <table class="exact-table">
            <thead>
              <tr>
                <th style="width: 45px; text-align: center;">S.No</th>
                <th style="width: 140px;">Roll Number</th>
                <th>Student Name</th>
                <th style="width: 90px; text-align: center;">CGPA</th>
              </tr>
            </thead>
            <tbody>
              ${Array.from({ length: 15 }).map((_, i) => {
                const s = p1List[i];
                if (!s) return `<tr><td style="text-align:center;">${i+1}.</td><td></td><td></td><td></td></tr>`;
                const isFail = (s.backlog_count > 0) || (s.cgpa === null && s.sgpa === null);
                const cgpaVal = s.cgpa || s.sgpa;
                const cgpaStr = (isSlow && isFail) ? 'Fail' : (cgpaVal !== null && cgpaVal !== undefined ? Number(cgpaVal).toFixed(2) : '-');
                return `
                  <tr>
                    <td style="text-align: center;">${i+1}.</td>
                    <td>${s.roll_number || ''}</td>
                    <td><b>${s.student_name || ''}</b></td>
                    <td style="text-align: center;">${cgpaStr}</td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
        <div class="page-footer-sig">Signature of the faculty</div>
      </div>
    `;

    // ===== PAGE 2: Faculty Observation =====
    html += `
      <div class="paper-page">
        <div>
          ${buildHeaderHtml(`${tierTitle} – Based on the Faculty Observation`, true)}
          <table class="exact-table">
            <thead>
              <tr>
                <th style="width: 45px; text-align: center;">S.No</th>
                <th style="width: 150px;">Roll Number</th>
                <th>Student Name</th>
                <th style="width: 120px; text-align: center;">Signature of the faculty</th>
              </tr>
            </thead>
            <tbody>
              ${Array.from({ length: 15 }).map((_, i) => {
                const s = p2List[i];
                if (!s) return `<tr><td style="text-align:center;">${i+1}.</td><td></td><td></td><td></td></tr>`;
                return `
                  <tr>
                    <td style="text-align: center;">${i+1}.</td>
                    <td>${s.roll_number || ''}</td>
                    <td><b>${s.student_name || ''}</b></td>
                    <td></td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
        <div class="page-footer-sig">Signature of the faculty</div>
      </div>
    `;

    // ===== PAGE 3: CIE 1 Evaluation =====
    html += `
      <div class="paper-page">
        <div>
          ${buildHeaderHtml(`${tierTitle} – Based on the CIE 1 Evaluation`, true)}
          <table class="exact-table">
            <thead>
              <tr>
                <th style="width: 45px; text-align: center;">S.No</th>
                <th style="width: 140px;">Roll Number</th>
                <th>Student Name</th>
                <th style="width: 110px; text-align: center;">CIE 1 MARKS</th>
              </tr>
            </thead>
            <tbody>
              ${Array.from({ length: 15 }).map((_, i) => {
                const s = p3List[i];
                if (!s) return `<tr><td style="text-align:center;">${i+1}.</td><td></td><td></td><td></td></tr>`;
                const cieStr = s.cie_marks !== null && s.cie_marks !== undefined ? s.cie_marks : '-';
                return `
                  <tr>
                    <td style="text-align: center;">${i+1}.</td>
                    <td>${s.roll_number || ''}</td>
                    <td><b>${s.student_name || ''}</b></td>
                    <td style="text-align: center; font-weight: bold;">${cieStr}</td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
        <div class="page-footer-sig">Signature of the faculty</div>
      </div>
    `;

    html += `</div>`;
    container.innerHTML = html;

  } else {
    // Comprehensive Report View
    container.innerHTML = `
      <div class="paper-page">
        <div>
          ${buildHeaderHtml('Comprehensive 3-Tier Academic Audit & Performance Report', true)}
          <table class="exact-table">
            <thead>
              <tr>
                <th style="width: 35px; text-align: center;">#</th>
                <th style="width: 115px;">Roll No</th>
                <th>Student Name</th>
                <th style="width: 45px; text-align: center;">CIE</th>
                <th style="width: 50px; text-align: center;">CGPA</th>
                <th style="width: 75px; text-align: center;">Category</th>
                <th>Action Plan</th>
              </tr>
            </thead>
            <tbody>
              ${state.allStudents.map((s, idx) => `
                <tr>
                  <td style="text-align:center;">${idx + 1}</td>
                  <td>${s.roll_number}</td>
                  <td><b>${s.student_name}</b></td>
                  <td style="text-align:center;">${s.cie_marks !== null && s.cie_marks !== undefined ? s.cie_marks : '-'}</td>
                  <td style="text-align:center;">${s.cgpa || s.sgpa || '-'}</td>
                  <td style="text-align:center; font-weight:bold; color:${s.tier === 'Advanced' ? '#16a34a' : (s.tier === 'Slow' ? '#dc2626' : '#0284c7')}">${s.tier}</td>
                  <td style="font-size:0.75rem;">${s.action_plan || '-'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:30px; font-weight:bold; font-size:0.85rem;">
          <div>Faculty Incharge</div>
          <div>Program Coordinator</div>
          <div>Head of the Department (HOD)</div>
        </div>
      </div>
    `;
  }
}

function triggerDirectDownload(reportType, format, students, metadata) {
  // Call prepare-download API to save on server and get direct static URL
  fetch('/api/prepare-download', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      report_type: reportType,
      metadata: metadata,
      students: students,
      statistics: state.classified ? state.classified.statistics : null
    })
  })
  .then(res => res.json())
  .then(data => {
    if (data.status === 'success') {
      const downloadUrl = (format === 'pdf') ? data.pdf_url : data.docx_url;
      const downloadName = (format === 'pdf') ? data.pdf_filename : data.docx_filename;
      
      const link = document.createElement('a');
      link.href = downloadUrl + '?v=' + Date.now();
      link.download = downloadName;
      document.body.appendChild(link);
      link.click();
      setTimeout(() => {
        if (link.parentNode) link.parentNode.removeChild(link);
      }, 1000);

      showToast(`Downloaded: ${downloadName}`, 'success');
    } else {
      throw new Error(data.detail || 'Download preparation failed');
    }
  })
  .catch(err => {
    console.error('Download fallback to direct form POST:', err);
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/api/download-direct';
    form.style.display = 'none';

    const fields = {
      report_type: reportType,
      format: format,
      metadata_json: JSON.stringify(metadata),
      students_json: JSON.stringify(students)
    };

    for (const key in fields) {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = key;
      input.value = fields[key];
      form.appendChild(input);
    }

    document.body.appendChild(form);
    form.submit();
    setTimeout(() => {
      if (form.parentNode) form.parentNode.removeChild(form);
    }, 2000);
  });
}

async function downloadDocument(format) {
  const isAdv = (state.activeReportTab === 'advanced');
  const isSlow = (state.activeReportTab === 'slow');
  const reportType = isAdv ? 'advanced' : (isSlow ? 'slow' : 'comprehensive');
  const targetStudents = isAdv ? state.classified.advanced_learners : (isSlow ? state.classified.slow_learners : state.allStudents);

  const cleanAy = (state.metadata.academic_year || '2024-25').replace(/[\/\\]/g, '-');
  const tierName = isAdv ? 'Advance_learners' : (isSlow ? 'Slow_learners' : 'Comprehensive_Report');
  const expectedName = `CSE_${cleanAy}_C_${tierName}_template.${format}`;

  showToast(`Preparing ${expectedName}...`, 'info');
  triggerDirectDownload(reportType, format, targetStudents, state.metadata);
}

async function exportToExcel() {
  const cleanAy = (state.metadata.academic_year || '2024-25').replace(/[\/\\]/g, '-');
  const expectedName = `CSE_${cleanAy}_C_Student_Performance.xlsx`;
  showToast(`Downloading: ${expectedName}`, 'info');

  try {
    triggerDirectDownload('comprehensive', 'xlsx', state.allStudents, state.metadata);
    showToast(`Download started: ${expectedName}`, 'success');
  } catch (err) {
    showToast('Excel export failed: ' + err.message, 'error');
  }
}

