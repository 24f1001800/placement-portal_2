const { createApp, ref, computed, onMounted } = Vue;
const { createRouter, createWebHashHistory } = VueRouter;

axios.defaults.baseURL = 'http://127.0.0.1:5000/api';
axios.interceptors.request.use(config => {
    const activeToken = localStorage.getItem('token');
    if (activeToken) config.headers.Authorization = `Bearer ${activeToken}`;
    return config;
});

const Home = {
    template: `
        <div class="container text-center mt-5 py-5">
            <div class="p-5 mb-4 bg-light rounded-3 shadow-sm border">
                <div class="container-fluid py-5">
                    <h1 class="display-5 fw-bold text-primary">Campus Recruitment Portal</h1>
                    <p class="col-md-8 fs-4 mx-auto text-muted">Automated execution matrices matching academic talents with corporate career openings.</p>
                    <div class="d-flex justify-content-center gap-3 mt-4" v-if="!isLoggedIn">
                        <router-link to="/login" class="btn btn-primary btn-lg px-4">Sign In</router-link>
                        <router-link to="/register" class="btn btn-outline-success btn-lg px-4">Create Account</router-link>
                    </div>
                </div>
            </div>
        </div>
    `,
    setup() { return { isLoggedIn: ref(!!localStorage.getItem('token')) }; }
};

const ChangePasswordPanel = {
    template: `
        <div class="card shadow-sm border-danger mt-4">
            <div class="card-header bg-danger text-white py-2"><h6 class="mb-0"><i class="bi bi-shield-lock-fill me-2"></i>Account Security</h6></div>
            <div class="card-body">
                <form @submit.prevent="updatePassword">
                    <div class="mb-2"><label class="small fw-bold text-secondary">Current Password</label><input type="password" v-model="passwords.current_password" class="form-control form-control-sm" required></div>
                    <div class="mb-2"><label class="small fw-bold text-secondary">New Password</label><input type="password" v-model="passwords.new_password" class="form-control form-control-sm" minlength="6" placeholder="Min 6 characters" required></div>
                    <button class="btn btn-danger btn-sm w-100 mt-2">Update Security Token</button>
                </form>
            </div>
        </div>
    `,
    setup() {
        const passwords = ref({ current_password: '', new_password: '' });
        const updatePassword = async () => {
            try {
                await axios.post('/auth/change-password', passwords.value);
                alert("Security configuration updated!");
                passwords.value = { current_password: '', new_password: '' };
            } catch (err) { alert(err.response?.data?.message || "Password modification rejected."); }
        };
        return { passwords, updatePassword };
    }
};

const Login = {
    template: `
        <div class="container mt-5"><div class="row justify-content-center"><div class="col-md-5"><div class="card shadow border-0">
            <div class="card-header bg-primary text-white text-center py-3"><h4 class="mb-0">Account Login</h4></div>
            <div class="card-body p-4"><form @submit.prevent="handleLogin">
                <div class="mb-3"><label class="form-label fw-bold">Email Address</label><input type="email" v-model="email" class="form-control" required></div>
                <div class="mb-3"><label class="form-label fw-bold">Password</label><input type="password" v-model="password" class="form-control" required></div>
                <div v-if="errorMessage" class="alert alert-danger py-2 small text-center">{{ errorMessage }}</div>
                <button type="submit" class="btn btn-primary w-100 py-2 fw-bold">Sign In</button>
            </form></div>
        </div></div></div></div>
    `,
    setup() {
        const email = ref(''), password = ref(''), errorMessage = ref('');
        const handleLogin = async () => {
            try {
                const res = await axios.post('/auth/login', { email: email.value, password: password.value });
                localStorage.setItem('token', res.data.token);
                localStorage.setItem('role', res.data.role);
                window.location.hash = res.data.role === 'admin' ? '#/admin-dashboard' : (res.data.role === 'company' ? '#/company-dashboard' : '#/student-dashboard');
                window.location.reload();
            } catch (err) { errorMessage.value = err.response?.data?.message || 'Authentication error.'; }
        };
        return { email, password, errorMessage, handleLogin };
    }
};

const Register = {
    template: `
        <div class="container mt-5"><div class="row justify-content-center"><div class="col-md-6"><div class="card shadow border-0">
            <div class="card-header bg-success text-white text-center py-3"><h4 class="mb-0">Create Profile Identity</h4></div>
            <div class="card-body p-4"><form @submit.prevent="handleRegister">
                <div class="mb-3"><label class="form-label fw-bold">Select Role</label><select v-model="role" class="form-select"><option value="student">Student Graduate</option><option value="company">Corporate Recruiter</option></select></div>
                <div v-if="role === 'company'" class="mb-3 p-3 bg-light border rounded">
                    <label class="form-label fw-bold text-success">Official Corporate Title</label><input type="text" v-model="companyName" class="form-control mb-2" required>
                    <label class="form-label fw-bold text-success">Industry</label><input type="text" v-model="industry" class="form-control mb-2" placeholder="e.g. IT Services, Finance...">
                    <label class="form-label fw-bold text-success">Location</label><input type="text" v-model="location" class="form-control" placeholder="e.g. Bangalore, India">
                </div>
                <div class="mb-3"><label class="form-label fw-bold">Email Address</label><input type="email" v-model="email" class="form-control" required></div>
                <div class="mb-3"><label class="form-label fw-bold">Password</label><input type="password" v-model="password" class="form-control" minlength="6" required></div>
                <div v-if="successMessage" class="alert alert-success py-2 text-center small">{{ successMessage }}</div>
                <div v-if="errorMessage" class="alert alert-danger py-2 text-center small">{{ errorMessage }}</div>
                <button type="submit" class="btn btn-success w-100 py-2 fw-bold">Register Identity</button>
            </form></div>
        </div></div></div></div>
    `,
    setup() {
        const role = ref('student'), email = ref(''), password = ref(''), companyName = ref('');
        const industry = ref(''), location = ref('');
        const errorMessage = ref(''), successMessage = ref('');
        const handleRegister = async () => {
            try {
                const payload = {
                    email: email.value, password: password.value, role: role.value,
                    ...(role.value === 'company' && { company_name: companyName.value, industry: industry.value, location: location.value })
                };
                const res = await axios.post('/auth/register', payload);
                successMessage.value = res.data.message;
            } catch (err) { errorMessage.value = err.response?.data?.message || 'Registration failure.'; }
        };
        return { role, email, password, companyName, industry, location, errorMessage, successMessage, handleRegister };
    }
};

const AdminDashboard = {
    template: `
        <div class="container mt-4 mb-5">
            <h2 class="mb-4 border-bottom pb-2">Administration Command Center <span class="badge bg-secondary font-monospace small" style="font-size:0.9rem;">Redis Cached Stats Layer Active</span></h2>
            <div class="row mb-5 g-4">
                <div class="col-md-4"><div class="card bg-primary text-white p-3 shadow border-0"><h5>Total Students</h5><h2 class="mb-0 fw-bold">{{ stats.total_students }}</h2></div></div>
                <div class="col-md-4"><div class="card bg-success text-white p-3 shadow border-0"><h5>Registered Employers</h5><h2 class="mb-0 fw-bold">{{ stats.total_companies }}</h2></div></div>
                <div class="col-md-4"><div class="card bg-dark text-white p-3 shadow border-0"><h5>Approved Drives</h5><h2 class="mb-0 fw-bold">{{ stats.total_drives }}</h2></div></div>
            </div>

            <div class="card shadow border-0 mb-5">
                <div class="card-header bg-warning py-3 fw-bold text-dark">Pending Corporate Profiles Verification</div>
                <div class="card-body p-3">
                    <div v-if="pendingCompanies.length === 0" class="text-center text-muted py-3">No profiles awaiting clearance.</div>
                    <div v-else class="list-group">
                        <div v-for="c in pendingCompanies" :key="c.id" class="list-group-item d-flex justify-content-between align-items-center bg-white border mb-2 p-3 rounded-3 shadow-sm transition-all hover-shadow">
                            <div>
                                <h6 class="mb-1 fw-bold text-dark">{{ c.company_name }}</h6>
                                <small class="text-muted"><i class="bi bi-envelope me-1"></i>{{ c.email }}</small>
                            </div>
                            <div class="d-flex gap-2">
                                <button class="btn btn-sm btn-success px-3 fw-bold shadow-sm" @click="approveCompany(c.id)">Grant Access</button>
                                <button class="btn btn-sm btn-outline-danger px-3 fw-bold" @click="rejectCompany(c.id)">Reject</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card shadow border-0 mb-5">
                <div class="card-header bg-dark text-white py-3 fw-bold">Pending Job Campaign Approvals</div>
                <div class="card-body p-3">
                    <div v-if="pendingDrives.length === 0" class="text-center text-muted py-3">All campaigns processed.</div>
                    <div v-else class="list-group">
                        <div v-for="d in pendingDrives" :key="d.id" class="list-group-item d-flex justify-content-between align-items-center bg-white border mb-2 p-3 rounded-3 shadow-sm transition-all hover-shadow">
                            <div>
                                <h6 class="mb-1 fw-bold text-dark">{{ d.job_title }}</h6>
                                <small class="text-muted">Partner Employer: <strong>{{ d.company_name }}</strong> | Criteria Cutoff: <strong>{{ d.cgpa_eligibility }} CGPA</strong></small>
                            </div>
                            <div class="d-flex gap-2">
                                <button class="btn btn-sm btn-primary px-3 fw-bold shadow-sm" @click="approveDrive(d.id)">Approve</button>
                                <button class="btn btn-sm btn-outline-danger px-3 fw-bold" @click="rejectDrive(d.id)">Reject</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card shadow border-0 mb-5">
                <div class="card-header bg-info text-white py-3 fw-bold">Search & Manage Companies</div>
                <div class="card-body p-3">
                    <input type="text" v-model="companySearch" @input="searchCompanies" class="form-control mb-3" placeholder="🔍 Search by company name or industry...">
                    <table class="table align-middle mb-0">
                        <thead><tr><th>Name</th><th>Email</th><th>Approval</th><th>Account</th><th>Actions</th></tr></thead>
                        <tbody>
                            <tr v-for="c in allCompanies" :key="c.id">
                                <td>{{ c.company_name }}</td>
                                <td>{{ c.email }}</td>
                                <td><span :class="c.is_approved ? 'badge bg-success' : 'badge bg-warning text-dark'">{{ c.is_approved ? 'Approved' : 'Pending' }}</span></td>
                                <td><span :class="c.is_active ? 'badge bg-success' : 'badge bg-dark'">{{ c.is_active ? 'Active' : 'Blacklisted' }}</span></td>
                                <td><button class="btn btn-sm btn-outline-dark" @click="toggleCompanyActive(c.user_id)">{{ c.is_active ? 'Blacklist' : 'Reactivate' }}</button></td>
                            </tr>
                            <tr v-if="allCompanies.length === 0"><td colspan="5" class="text-center text-muted py-3">No matching companies.</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="card shadow border-0">
                <div class="card-header bg-info text-white py-3 fw-bold">Search & Manage Students</div>
                <div class="card-body p-3">
                    <input type="text" v-model="studentSearch" @input="searchStudents" class="form-control mb-3" placeholder="🔍 Search by name, email, contact, or ID...">
                    <table class="table align-middle mb-0">
                        <thead><tr><th>Name</th><th>Email</th><th>Branch</th><th>CGPA</th><th>Account</th><th>Actions</th></tr></thead>
                        <tbody>
                            <tr v-for="s in allStudents" :key="s.id">
                                <td>{{ s.name }}</td><td>{{ s.email }}</td><td>{{ s.branch }}</td><td>{{ s.cgpa }}</td>
                                <td><span :class="s.is_active ? 'badge bg-success' : 'badge bg-dark'">{{ s.is_active ? 'Active' : 'Blacklisted' }}</span></td>
                                <td><button class="btn btn-sm btn-outline-dark" @click="toggleStudentActive(s.id)">{{ s.is_active ? 'Blacklist' : 'Reactivate' }}</button></td>
                            </tr>
                            <tr v-if="allStudents.length === 0"><td colspan="6" class="text-center text-muted py-3">No matching students.</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `,
    setup() {
        const stats = ref({}), pendingCompanies = ref([]), pendingDrives = ref([]);
        const allCompanies = ref([]), allStudents = ref([]);
        const companySearch = ref(''), studentSearch = ref('');

        const load = async () => {
            stats.value = (await axios.get('/admin/dashboard')).data;
            pendingCompanies.value = (await axios.get('/admin/companies/pending')).data;
            pendingDrives.value = (await axios.get('/admin/drives/pending')).data;
            searchCompanies();
            searchStudents();
        };
        const approveCompany = async id => { await axios.post(`/admin/companies/approve/${id}`); load(); };
        const rejectCompany = async id => { if (!confirm('Reject and remove this company registration?')) return; await axios.post(`/admin/companies/reject/${id}`); load(); };
        const approveDrive = async id => { await axios.post(`/admin/drives/approve/${id}`); load(); };
        const rejectDrive = async id => { if (!confirm('Reject this placement drive?')) return; await axios.post(`/admin/drives/reject/${id}`); load(); };
        const searchCompanies = async () => { allCompanies.value = (await axios.get('/admin/companies', { params: { q: companySearch.value } })).data; };
        const searchStudents = async () => { allStudents.value = (await axios.get('/admin/students', { params: { q: studentSearch.value } })).data; };
        const toggleCompanyActive = async userId => { await axios.post(`/admin/companies/toggle-active/${userId}`); searchCompanies(); };
        const toggleStudentActive = async userId => { await axios.post(`/admin/students/toggle-active/${userId}`); searchStudents(); };

        onMounted(load);
        return {
            stats, pendingCompanies, pendingDrives, allCompanies, allStudents, companySearch, studentSearch,
            approveCompany, rejectCompany, approveDrive, rejectDrive, searchCompanies, searchStudents,
            toggleCompanyActive, toggleStudentActive
        };
    }
};

const CompanyDashboard = {
    template: `
        <div class="container mt-4 mb-5">
            <div class="p-4 bg-white rounded shadow-sm border mb-4 d-flex justify-content-between align-items-center">
                <div><h2>{{ profile.name }} Console Workspace</h2></div>
                <div class="d-flex gap-2">
                    <button class="btn btn-outline-dark fw-bold btn-sm" @click="triggerCsvExport" :disabled="exportLoading">
                        <i class="bi bi-file-earmark-spreadsheet me-1"></i>
                        {{ exportLoading ? 'Celery Assembling CSV...' : 'Async CSV Export Applicants' }}
                    </button>
                    <a v-if="downloadUrl" :href="'http://127.0.0.1:5000' + downloadUrl" target="_blank" class="btn btn-success fw-bold btn-sm">💾 Download Compiled CSV File</a>
                </div>
            </div>
            <div v-if="!profile.is_approved" class="alert alert-warning">Awaiting deployment authorization checks from Administration executives.</div>
            <div class="row g-4" v-else>
                <div class="col-lg-4">
                    <div class="card p-4 shadow-sm bg-light border-0">
                        <h4 class="mb-3 text-success border-bottom pb-2">Launch Open Campaign</h4>
                        <form @submit.prevent="createDrive">
                            <div class="mb-2"><label class="small fw-bold">Designation</label><input type="text" v-model="form.job_title" class="form-control" required></div>
                            <div class="mb-2"><label class="small fw-bold">Specs</label><textarea v-model="form.description" class="form-control" rows="2" required></textarea></div>
                            <div class="mb-2"><label class="small fw-bold">Branches</label><input type="text" v-model="form.branch_eligibility" class="form-control" required></div>
                            <div class="mb-2"><label class="small fw-bold">Cutoff</label><input type="number" step="0.01" min="0" max="10" v-model="form.cgpa_eligibility" class="form-control" required></div>
                            <div class="mb-3"><label class="small fw-bold">Deadline Target</label><input type="date" v-model="form.deadline" class="form-control" required></div>
                            <button class="btn btn-success w-100 fw-bold">Submit Setup File</button>
                        </form>
                    </div>
                    <change-password-panel></change-password-panel>
                </div>
                <div class="col-lg-8">
                    <div class="card shadow-sm mb-4"><div class="card-header bg-dark text-white fw-bold">Your Deployment History</div><div class="card-body p-0">
                        <table class="table align-middle mb-0"><thead><tr><th>Role</th><th>Status</th><th>Deadline</th></tr></thead><tbody>
                        <tr v-for="d in drives"><td>{{ d.job_title }}</td><td><span class="badge bg-secondary">{{ d.status }}</span></td><td>{{ d.deadline }}</td></tr>
                        </tbody></table>
                    </div></div>
                    <div class="card shadow-sm"><div class="card-header bg-secondary text-white fw-bold">Candidate Evaluation and Interview Scheduling Pipeline</div><div class="card-body p-0">
                        <table class="table align-middle mb-0"><thead><tr><th>Applicant Name</th><th>Job Target</th><th>Current State Status</th><th>Set Interview Schedule Target</th></tr></thead><tbody>
                        <tr v-for="a in applicants">
                            <td>{{ a.student_name }} ({{ a.branch }} - {{ a.cgpa }} CGPA)<br><a :href="'http://127.0.0.1:5000' + a.resume_url" target="_blank" v-if="a.resume_url" class="small text-decoration-none">📂 Open Local Resume File</a></td>
                            <td>{{ a.job_title }}</td>
                            <td>
                                <select v-model="a.status" class="form-select form-select-sm" @change="updateApplicantState(a.application_id, a.status, a.interview_date)">
                                    <option value="Applied">Applied</option><option value="Shortlisted">Shortlisted</option><option value="Selected">Selected</option><option value="Rejected">Rejected</option>
                                </select>
                            </td>
                            <td>
                                <input type="date" v-model="a.interview_date" class="form-control form-control-sm" @change="updateApplicantState(a.application_id, a.status, a.interview_date)">
                                <small v-if="a.interview_date" class="text-success small">Scheduled: {{a.interview_date}}</small>
                            </td>
                        </tr>
                        <tr v-if="applicants.length === 0"><td colspan="4" class="text-center text-muted py-3">No candidates found in the active filtering scope rows.</td></tr>
                        </tbody></table>
                    </div></div>
                </div>
            </div>
        </div>
    `,
    components: { ChangePasswordPanel },
    setup() {
        const profile = ref({}), drives = ref([]), applicants = ref([]), downloadUrl = ref(null), exportLoading = ref(false);
        const form = ref({ job_title: '', description: '', branch_eligibility: '', cgpa_eligibility: '', deadline: '' });

        const load = async () => {
            profile.value = (await axios.get('/company/profile')).data;
            if (profile.value.is_approved) {
                drives.value = (await axios.get('/company/drives')).data;
                applicants.value = (await axios.get('/company/applicants')).data;
            }
        };
        const createDrive = async () => {
            try {
                await axios.post('/company/drives', form.value);
                alert("Recruitment strategy locked!"); load();
            } catch (err) { alert(err.response?.data?.message || "Invalid setup params."); }
        };
        const updateApplicantState = async (appId, statusStr, dateStr) => {
            await axios.post('/company/applicants/review', { application_id: appId, status: statusStr, interview_date: dateStr });
        };
        const triggerCsvExport = async () => {
            exportLoading.value = true; downloadUrl.value = null;
            try {
                const res = await axios.post('/company/export-applicants');
                const taskId = res.data.task_id;

                const checkTimer = setInterval(async () => {
                    try {
                        const statusRes = await axios.get(`/company/export-status/${taskId}`);
                        if (statusRes.data.status === 'COMPLETED') {
                            clearInterval(checkTimer);
                            downloadUrl.value = statusRes.data.download_url;
                            exportLoading.value = false;
                        } else if (statusRes.data.status === 'FAILED') {
                            clearInterval(checkTimer);
                            exportLoading.value = false;
                            alert("Export failed on the server. Please try again.");
                        }
                    } catch (err) {
                        clearInterval(checkTimer);
                        exportLoading.value = false;
                        alert("Lost connection while checking export status.");
                    }
                }, 1500);
            } catch (err) {
                exportLoading.value = false;
                alert("Export configuration fault.");
            }
        };
        onMounted(load); return { profile, drives, applicants, form, downloadUrl, exportLoading, createDrive, updateApplicantState, triggerCsvExport };
    }
};

const StudentDashboard = {
    template: `
        <div class="container mt-4 mb-5"><div class="row g-4">
            <div class="col-lg-4">
                <div class="card shadow border-0 rounded overflow-hidden mb-3"><div class="card-header bg-success text-white py-3 fw-bold">Academic Portfolio Context</div><div class="card-body bg-light">
                    <form @submit.prevent="saveProfile">
                        <div class="mb-2"><label class="small fw-bold">Name</label><input type="text" v-model="profile.name" class="form-control" required></div>
                        <div class="mb-2"><label class="small fw-bold">Branch Code</label><input type="text" v-model="profile.branch" class="form-control" required></div>
                        <div class="mb-2"><label class="small fw-bold">CGPA</label><input type="number" step="0.01" min="0" max="10" v-model="profile.cgpa" class="form-control" required></div>
                        <div class="mb-2"><label class="small fw-bold">Year of Study</label><input type="number" min="1" max="5" v-model="profile.year" class="form-control" required></div>
                        <div class="mb-3"><label class="small fw-bold">Contact Number</label><input type="text" v-model="profile.contact" class="form-control" placeholder="For placement cell use"></div>
                        <button class="btn btn-success btn-sm w-100 py-2 fw-bold">Save Metrics Profile</button>
                    </form>
                    <hr>
                    <div class="mb-2"><label class="small fw-bold text-primary">Upload Official Resume (PDF/Docs Only)</label><input type="file" ref="resumeFile" class="form-control form-control-sm" @change="uploadFile"></div>
                    <div v-if="profile.resume_url" class="alert alert-info py-1 small text-center mt-2"><a :href="'http://127.0.0.1:5000' + profile.resume_url" target="_blank" class="text-decoration-none fw-bold">📄 View Uploaded Resume File</a></div>
                </div></div>

                <div class="card shadow border-0 mb-3" v-if="placements.length > 0">
                    <div class="card-header bg-success text-white py-2 fw-bold small"><i class="bi bi-award-fill me-2"></i>Placement Confirmations</div>
                    <div class="card-body bg-white p-3">
                        <div v-for="p in placements" :key="p.id" class="border rounded p-2 mb-2">
                            <div class="fw-bold">{{ p.position }} @ {{ p.company_name }}</div>
                            <a :href="'http://127.0.0.1:5000' + p.offer_letter_url" target="_blank" class="btn btn-sm btn-outline-success mt-1">📄 View / Download Offer Letter</a>
                        </div>
                    </div>
                </div>

                <div class="card shadow border-0 mb-3">
                    <div class="card-header bg-dark text-white py-2 fw-bold small"><i class="bi bi-file-earmark-spreadsheet me-2"></i>Data Export Utilities</div>
                    <div class="card-body bg-white p-3">
                        <button class="btn btn-outline-dark btn-sm w-100 fw-bold mb-2" @click="triggerStudentCsvExport" :disabled="exportLoading">
                            <i class="bi bi-cloud-arrow-down-fill me-1"></i>
                            {{ exportLoading ? 'Assembling History Log...' : 'Async CSV Export History' }}
                        </button>
                        <a v-if="downloadUrl" :href="'http://127.0.0.1:5000' + downloadUrl" target="_blank" class="btn btn-success btn-sm w-100 fw-bold shadow-sm">💾 Download Compiled History CSV</a>
                    </div>
                </div>

                <change-password-panel></change-password-panel>
            </div>
            <div class="col-lg-8">
                <div class="card shadow-sm mb-3 bg-white border-start border-primary border-4"><div class="card-body py-2"><div class="row g-2 align-items-center">
                    <div class="col-md-7"><input type="text" v-model="filters.searchQuery" class="form-control form-control-sm" placeholder="🔍 Search roles or corporate companies..."></div>
                    <div class="col-md-5 d-flex align-items-center justify-content-end"><label class="small text-nowrap me-2 mb-0">Max CGPA Threshold: <strong>{{ filters.maxCgpa }}</strong></label><input type="range" class="form-range w-50" min="0" max="10" step="0.5" v-model="filters.maxCgpa"></div>
                </div></div></div>
                <div class="card shadow border-0 mb-4"><div class="card-header bg-primary text-white py-3 fw-bold">Open Verified Corporate Openings</div><div class="card-body">
                    <p v-if="filteredDrives.length === 0" class="text-center text-muted">No matching drives align with your parameter filters.</p>
                    <div v-for="d in filteredDrives" :key="d.id" class="p-3 border rounded mb-2 bg-light">
                        <div class="d-flex justify-content-between"><h5>{{ d.job_title }} - <small class="text-secondary">{{ d.company_name }}</small></h5><button class="btn btn-sm btn-outline-primary" @click="apply(d.id)">Apply Now</button></div>
                        <p class="small text-muted my-1">{{ d.description }}</p>
                        <small class="badge bg-white text-dark border">Requires CGPA >= {{ d.cgpa_eligibility }} ({{ d.branch_eligibility }})</small>
                        <small class="text-danger fw-bold ms-3">Closing Deadline: {{ d.deadline }}</small>
                    </div>
                </div></div>
                <div class="card shadow border-0"><div class="card-header bg-dark text-white py-3 fw-bold">Track Your Applications Status Dashboard</div><div class="card-body p-0">
                    <table class="table align-middle mb-0"><thead><tr><th>Target Corporation</th><th>Position Designation</th><th>Current Pipeline Status</th><th>Scheduled Evaluation Date</th></tr></thead><tbody>
                    <tr v-for="a in applications">
                        <td class="fw-bold">{{ a.company_name }}</td><td>{{ a.job_title }}</td>
                        <td><span class="badge bg-warning text-dark">{{ a.status }}</span></td>
                        <td><span v-if="a.interview_date" class="badge bg-success"><i class="bi bi-calendar-event me-1"></i> Interview: {{ a.interview_date }}</span><span v-else class="text-muted small">Not Scheduled</span></td>
                    </tr>
                    </tbody></table>
                </div></div>
            </div>
        </div></div>
    `,
    components: { ChangePasswordPanel },
    setup() {
        const profile = ref({ name: '', branch: '', cgpa: 0.0, year: 4, contact: '', resume_url: '' }), drives = ref([]), applications = ref([]), placements = ref([]), resumeFile = ref(null);
        const filters = ref({ searchQuery: '', maxCgpa: 10.0 });
        const downloadUrl = ref(null), exportLoading = ref(false);

        const load = async () => {
            profile.value = (await axios.get('/student/profile')).data;
            drives.value = (await axios.get('/student/drives/approved')).data;
            applications.value = (await axios.get('/student/applications')).data;
            placements.value = (await axios.get('/student/placements')).data;
        };
        const filteredDrives = computed(() => {
            return drives.value.filter(d => {
                const s = filters.value.searchQuery.toLowerCase();
                return (d.job_title.toLowerCase().includes(s) || d.company_name.toLowerCase().includes(s)) && d.cgpa_eligibility <= parseFloat(filters.value.maxCgpa);
            });
        });
        const saveProfile = async () => {
            try {
                if (parseFloat(profile.value.cgpa) < 0 || parseFloat(profile.value.cgpa) > 10) return alert("CGPA bounds out of scale.");
                await axios.post('/student/profile', profile.value); alert("Profile cached safely!"); load();
            } catch (err) { alert("Profile configuration parameter verification mismatch."); }
        };
        const uploadFile = async (e) => {
            const file = e.target.files[0]; if (!file) return;
            const formData = new FormData(); formData.append('resume', file);
            const res = await axios.post('/student/upload-resume', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
            alert(res.data.message); load();
        };
        const apply = async id => { try { const res = await axios.post('/student/apply', { drive_id: id }); alert(res.data.message); load(); } catch(err) { alert(err.response?.data?.message || "Rejected."); } };

        const triggerStudentCsvExport = async () => {
            exportLoading.value = true; downloadUrl.value = null;
            try {
                const res = await axios.post('/student/export-history');
                const taskId = res.data.task_id;

                const checkTimer = setInterval(async () => {
                    try {
                        const statusRes = await axios.get(`/student/export-status/${taskId}`);
                        if (statusRes.data.status === 'COMPLETED') {
                            clearInterval(checkTimer);
                            downloadUrl.value = statusRes.data.download_url;
                            exportLoading.value = false;
                        } else if (statusRes.data.status === 'FAILED') {
                            clearInterval(checkTimer);
                            exportLoading.value = false;
                            alert("Export failed on the server. Please try again.");
                        }
                    } catch (err) {
                        clearInterval(checkTimer);
                        exportLoading.value = false;
                        alert("Lost connection while checking export status.");
                    }
                }, 1500);
            } catch (err) {
                exportLoading.value = false;
                alert("Export configuration fault.");
            }
        };

        onMounted(load); return { profile, drives, filteredDrives, applications, placements, filters, resumeFile, saveProfile, uploadFile, apply, downloadUrl, exportLoading, triggerStudentCsvExport };
    }
};

const routes = [
    { path: '/', component: Home }, { path: '/login', component: Login }, { path: '/register', component: Register },
    { path: '/admin-dashboard', component: AdminDashboard }, { path: '/company-dashboard', component: CompanyDashboard }, { path: '/student-dashboard', component: StudentDashboard }
];
const router = createRouter({ history: createWebHashHistory(), routes });
const app = createApp({
    setup() {
        const token = ref(localStorage.getItem('token')), userRole = ref(localStorage.getItem('role')), isLoggedIn = computed(() => !!token.value);
        const executeSessionTermination = () => { localStorage.clear(); token.value = null; userRole.value = null; window.location.hash = '#/login'; window.location.reload(); };
        return { isLoggedIn, userRole, executeSessionTermination };
    }
});
app.use(router); app.mount('#app');