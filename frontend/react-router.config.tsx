// import type { Config } from "@react-router/dev/config";

// Option 1: Define your own type if needed
type Config = {
    ssr: boolean;
};

export default {
    ssr: false,
} satisfies Config;