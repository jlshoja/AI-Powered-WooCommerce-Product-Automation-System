<?php
/**
 * FTP Media Registration Script for WordPress
 *
 * Registers FTP-uploaded images as WordPress media attachments.
 * Upload this script to your WordPress root directory.
 *
 * Usage:
 *   php ftp-register-media.php [list_file.json]
 *
 * The list file should contain an array of objects:
 *   [{"filename": "image.webp", "url_path": "/wp-content/uploads/2026/07/image.webp"}]
 *
 * Results are written to [list_file].result.json
 */

// Load WordPress
require_once __DIR__ . '/wp-load.php';

// Check arguments
if ($argc < 2) {
    echo "Usage: php ftp-register-media.php <list_file.json>\n";
    echo "Example: php ftp-register-media.php output/ftp_register_20260723_194500.json\n";
    exit(1);
}

$list_file = $argv[1];

// Support both absolute and relative paths
if (!file_exists($list_file)) {
    // Try relative to WordPress root
    $list_file = __DIR__ . '/' . $list_file;
    if (!file_exists($list_file)) {
        echo "Error: File not found: $list_file\n";
        exit(1);
    }
}

// Read the file list
$json = file_get_contents($list_file);
$files = json_decode($json, true);
if (!$files || !is_array($files)) {
    echo "Error: Invalid JSON in $list_file\n";
    exit(1);
}

echo "Processing " . count($files) . " files...\n";

$results = [];
$upload_dir = wp_upload_dir();

foreach ($files as $item) {
    $filename = $item['filename'];
    $url_path = $item['url_path'];

    // Construct full server path
    $server_path = ABSPATH . ltrim($url_path, '/');

    if (!file_exists($server_path)) {
        echo "  SKIP: $filename - file not found at $server_path\n";
        $results[] = ['filename' => $filename, 'media_id' => null, 'error' => 'File not found'];
        continue;
    }

    // Check if already registered (by filename search)
    $existing = attachment_url_to_postid(home_url($url_path));
    if ($existing) {
        echo "  EXISTS: $filename -> media ID $existing\n";
        $results[] = ['filename' => $filename, 'media_id' => $existing];
        continue;
    }

    // Determine MIME type
    $mime_type = wp_check_filetype($filename)['type'] ?: 'image/jpeg';

    // Get file size
    $file_size = filesize($server_path);

    // Insert as media attachment
    $attachment_data = [
        'post_title'     => pathinfo($filename, PATHINFO_FILENAME),
        'post_mime_type' => $mime_type,
        'post_status'    => 'inherit',
        'post_content'   => '',
        'guid'           => home_url($url_path),
    ];

    $attachment_id = wp_insert_attachment($attachment_data, $server_path);

    if (is_wp_error($attachment_id)) {
        echo "  ERROR: $filename - " . $attachment_id->get_error_message() . "\n";
        $results[] = ['filename' => $filename, 'media_id' => null, 'error' => $attachment_id->get_error_message()];
        continue;
    }

    // Generate image meta
    $image_meta = wp_read_image_metadata($server_path);
    if ($image_meta) {
        wp_update_attachment_metadata($attachment_id, wp_generate_attachment_metadata($attachment_id, $server_path));
    }

    echo "  OK: $filename -> media ID $attachment_id\n";
    $results[] = ['filename' => $filename, 'media_id' => $attachment_id];
}

// Write results
$result_file = $list_file . '.result.json';
file_put_contents($result_file, json_encode($results, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
echo "\nResults written to: $result_file\n";
echo "Done! " . count(array_filter($results, fn($r) => $r['media_id'])) . " images registered.\n";
