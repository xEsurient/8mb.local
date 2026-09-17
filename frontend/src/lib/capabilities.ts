import type { PresetProfile } from './types';

/**
 * Normalizes a selected codec and profile against the effective capabilities.
 * 
 * @param selectedCodec The currently selected video codec.
 * @param selectedProfile The currently selected preset profile.
 * @param availableCodecs The effective list of enabled codecs from the backend.
 * @param presetProfiles The list of all preset profiles from the backend.
 * @returns A tuple of the normalized [codec, profile].
 */
export function normalizeCapabilities(
    selectedCodec: string | null,
    selectedProfile: PresetProfile | null,
    availableCodecs: string[],
    presetProfiles: PresetProfile[]
): [string | null, PresetProfile | null] {
    let newCodec = selectedCodec;
    let newProfile = selectedProfile;

    // 1. If we have a selected profile, but its codec is not available, we must normalize.
    if (newProfile && !availableCodecs.includes(newProfile.video_codec)) {
        // Try to find the first available profile
        const firstAvailableProfile = presetProfiles.find(p => p.available !== false && availableCodecs.includes(p.video_codec));
        if (firstAvailableProfile) {
            newProfile = firstAvailableProfile;
            newCodec = firstAvailableProfile.video_codec;
        } else {
            // No available profiles? Keep profile null.
            newProfile = null;
        }
    } else if (newProfile) {
        // Ensure codec matches the profile
        newCodec = newProfile.video_codec;
    }

    // 2. If we have no profile or we just invalidated it, ensure codec is valid
    if (newCodec && !availableCodecs.includes(newCodec)) {
        if (availableCodecs.length > 0) {
            newCodec = availableCodecs[0];
        } else {
            newCodec = null;
        }
    }

    // 3. Fallback: if codec is missing but available exists, pick first
    if (!newCodec && availableCodecs.length > 0) {
        newCodec = availableCodecs[0];
    }

    return [newCodec, newProfile];
}
