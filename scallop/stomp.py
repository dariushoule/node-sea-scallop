from rich import print


def invalidate_code_cache(sea_resource: bytes, code_cache: bytes) -> None:
    """
    This method invalidates the v8 code cache and resets expected_source_hash so cache hits are not rejected.

    *The v8 codepath (as of node23/24) looks something like:*

    ```
    CodeSerializer::Deserialize(...)
        ->
        const SerializedCodeData scd = SerializedCodeData::FromCachedData(
            isolate, 
            cached_data,
            SerializedCodeData::SourceHash(source, 
                                        wrapped_arguments,
                                        script_details.origin_options) // as expected_source_hash,
            &sanity_check_result);
            ->
            *rejection_result = scd.SanityCheck(
                Snapshot::ExtractReadOnlySnapshotChecksum(isolate->snapshot_blob()) // as expected_ro_snapshot_checksum,
                expected_source_hash);
                ->
                SanityCheckWithoutSource(expected_ro_snapshot_checksum);
                    * (CHECK?) ro_snapshot_checksum != expected_ro_snapshot_checksum
                    * (CHECK?) payload_length > max_payload_length
                    * (CHECK?) Checksum(ChecksummedContent()) != checksum
                    * (OK) :: all checks passed
                SanityCheckJustSource(expected_source_hash);
                    * (FAIL) :: source_hash != expected_source_hash
    ```

    *The code cache structure (as of node23/24) looks like:*

    ```
    //  kMagicNumberOffset = 0
    static const uint32_t kVersionHashOffset = kMagicNumberOffset + kUInt32Size;
    static const uint32_t kSourceHashOffset = kVersionHashOffset + kUInt32Size;
    static const uint32_t kFlagHashOffset = kSourceHashOffset + kUInt32Size;
    static const uint32_t kReadOnlySnapshotChecksumOffset =
        kFlagHashOffset + kUInt32Size;
    static const uint32_t kPayloadLengthOffset =
        kReadOnlySnapshotChecksumOffset + kUInt32Size;
    static const uint32_t kChecksumOffset = kPayloadLengthOffset + kUInt32Size;
    static const uint32_t kUnalignedHeaderSize = kChecksumOffset + kUInt32Size;
    static const uint32_t kHeaderSize = POINTER_SIZE_ALIGN(kUnalignedHeaderSize);
    ```
    """
    
    new_code_cache = bytearray(code_cache)
    expected_source_hash = int.from_bytes(code_cache[0x8:0xC], 'little')

    # Preserve HasWrappedArgumentsField and IsModuleField
    flags = expected_source_hash & 0xC0000000
    stomp_source_hash = flags | len(sea_resource)

    if stomp_source_hash != expected_source_hash:
        print('[teal][bold]* Source hash mismatch, stomping script[/bold][/teal]')
        new_code_cache[0x8:0xC] = stomp_source_hash.to_bytes(4, 'little')

    return bytes(new_code_cache)
    