function toggleContainer() {
    const downloadContainer = document.querySelector('.container_cdl');
    const info = document.querySelector('.info');
    const emp = document.querySelector('.empowerment');

    downloadContainer.classList.toggle('expanded');
    info.classList.toggle('showed');
    emp.classList.toggle('showed');
}