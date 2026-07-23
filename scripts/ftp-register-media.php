<?php
/**
 * FTP Media Registration Script for WordPress
 *
 * Registers FTP-uploaded images as WordPress media attachments.
 * Upload this script to your WordPress root directory.
 *
 * Supports two modes:
 *   1. CLI: php ftp-register-media.php <list_file.json>
 *   2. HTTP: POST https://yoursite.com/ftp-register-media.php
 *      Body: JSON array of {filename, url_path}
 *      Returns: JSON array of {filename, media_id}
 *
 * One-time setup: upload this file to WordPress root.
 * Then Python calls it automatically — no manual steps needed.
 */

// Load WordPress
require_once __DIR__ . '/wp-load.php';

// Determine mode: CLI or HTTP
$is_cli = php_sapi_name() === 'cli';

if ($is_cli) {
    // CLI mode
    if ($argc < 2) {
        echo "Usage: php ftp-register-media.php <list_file.json>\n";
        echo "Example: php ftp-register-media.php output/ftp_register_20260723_194500.json\n";
        exit(1);
    }

    $list_file = $argv[1];

    // Support both absolute and relative paths
    if (!file_exists($list_file)) {
        $list_file = __DIR__ . '/' . $list_file;
        if (!file_exists($list_file)) {
            echo "Error: File not found: $list_file\n";
            exit(1);
        }
    }

    $json = file_get_contents($list_file);
    $files = json_decode($json, true);
    if (!$files || !is_array($files)) {
        echo "Error: Invalid JSON in $list_file\n";
        exit(1);
    }
} else {
    // HTTP mode
    header('Content-Type: application/json; charset=utf-8');

    // Only accept POST
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        http_response_code(405);
        echo json_encode(['error' => 'POST required']);
        exit;
    }

    // Simple API key check (optional but recommended)
    $api_key = $_SERVER['HTTP_X_FTP_REGISTER_KEY'] ?? '';
    $expected_key = defined('FTP_REGISTER_API_KEY') ? FTP_REGISTER_API_KEY : '';
    if ($expected_key && $api_key !== $expected_key) {
        http_response_code(403);
        echo json_encode(['error' => 'Invalid API key']);
        exit;
    }

    // Read JSON body
    $raw = file_get_contents('php://input');
    $files = json_decode($raw, true);
    if (!$files || !is_array($files)) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid JSON body. Expected array of {filename, url_path}']);
        exit;
    }
}

// Process files
$results = [];

foreach ($files as $item) {
    $filename = $item['filename'] ?? '';
    $url_path = $item['url_path'] ?? '';

    if (!$filename || !$url_path) {
        $results[] = ['filename' => $filename, 'media_id' => null, 'error' => 'Missing filename or url_path'];
        continue;
    }

    // Construct full server path
    $server_path = ABSPATH . ltrim($url_path, '/');

    if (!file_exists($server_path)) {
        $results[] = ['filename' => $filename, 'media_id' => null, 'error' => 'File not found'];
        if ($is_cli) echo "  SKIP: $filename - file not found\n";
        continue;
    }

    // Check if already registered
    $existing = attachment_url_to_postid(home_url($url_path));
    if ($existing) {
        $results[] = ['filename' => $filename, 'media_id' => (int)$existing];
        if ($is_cli) echo "  EXISTS: $filename -> media ID $existing\n";
        continue;
    }

    // Determine MIME type
    $mime_type = wp_check_filetype($filename)['type'] ?: 'image/jpeg';

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
        $results[] = ['filename' => $filename, 'media_id' => null, 'error' => $attachment_id->get_error_message()];
        if ($is_cli) echo "  ERROR: $filename - " . $attachment_id->get_error_message() . "\n";
        continue;
    }

    // Generate image meta
    $image_meta = wp_read_image_metadata($server_path);
    if ($image_meta) {
        wp_update_attachment_metadata($attachment_id, wp_generate_attachment_metadata($attachment_id, $server_path));
    }

    $results[] = ['filename' => $filename, 'media_id' => (int)$attachment_id];
    if ($is_cli) echo "  OK: $filename -> media ID $attachment_id\n";
}

// Return results
$registered_count = count(array_filter($results, fn($r) => $r['media_id']));

if ($is_cli) {
    // CLI: write to file and print
    if (isset($list_file)) {
        $result_file = $list_file . '.result.json';
        file_put_contents($result_file, json_encode($results, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
        echo "\nResults written to: $result_file\n";
    }
    echo "Done! $registered_count images registered.\n";
} else {
    // HTTP: return JSON
    echo json_encode([
        'success' => true,
        'total' => count($files),
        'registered' => $registered_count,
        'results' => $results,
    ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
}
