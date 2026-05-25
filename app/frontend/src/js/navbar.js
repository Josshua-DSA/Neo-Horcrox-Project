document.addEventListener("DOMContentLoaded", function () {
  const sidebar = document.getElementById("sidebar");
  const menuBtn = document.getElementById("menuBtn");

  // Fungsi toggle sidebar (jika belum ada di file Anda)
  menuBtn.addEventListener("click", function (event) {
    sidebar.classList.toggle("active");
    // Mencegah event klik ini ikut memicu deteksi 'klik di luar' di bawah
    event.stopPropagation(); 
  });

  // Deteksi klik di seluruh dokumen
  document.addEventListener("click", function (event) {
    // Periksa apakah sidebar sedang terbuka (memiliki kelas 'active')
    if (sidebar.classList.contains("active")) {
      
      /* Jika target yang diklik BUKAN bagian dari sidebar 
        dan BUKAN juga bagian dari tombol menu, maka tutup sidebar.
      */
      if (!sidebar.contains(event.target) && !menuBtn.contains(event.target)) {
        sidebar.classList.remove("active");
      }
    }
  });
});