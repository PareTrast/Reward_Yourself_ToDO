// --- Add this to your index.html or a linked JS file ---

// Initialize Supabase JS Client (replace with your actual URL and anon key)
// Ensure this runs before the Flet app tries to call the functions below
const supabaseUrl = 'YOUR_SUPABASE_URL'; // Get from config or embed
const supabaseAnonKey = 'YOUR_SUPABASE_ANON_KEY'; // Get from config or embed
const supabase = supabase.createClient(supabaseUrl, supabaseAnonKey);

console.log("Supabase JS Client Initialized:", supabase);

// --- Wrapper Functions ---

async function jsSignUp(email, password, username) {
  console.log("JS: Attempting signup for email:", email);
  try {
    const { data, error } = await supabase.auth.signUp({
      email: email,
      password: password,
      options: {
        data: { // Metadata to store during signup
          username: username,
          user_medal_count: 0 // Example metadata
        }
      }
    });

    if (error) {
      console.error("JS SignUp Error:", error);
      // Return structure similar to Python version for consistency
      return { error: error.message, access_token: null, user_id: null, refresh_token: null };
    }

    console.log("JS SignUp Success:", data);
    // data contains session and user info upon successful signup (if email confirmation is off or handled)
    const session = data.session;
    const user = data.user;
    if (session && user) {
         return {
            error: null,
            access_token: session.access_token,
            user_id: user.id,
            refresh_token: session.refresh_token
         };
    } else if (user && !session) {
        // Signup might require email confirmation
        console.log("JS SignUp: User created but requires confirmation. No session returned.");
         return {
            error: "Confirmation required", // Special error message
            access_token: null,
            user_id: user.id, // Still return user ID if available
            refresh_token: null
         };
    } else {
        // Unexpected case
        console.error("JS SignUp: Unexpected response structure", data);
        return { error: "Unexpected signup response", access_token: null, user_id: null, refresh_token: null };
    }
  } catch (err) {
    console.error("JS SignUp Exception:", err);
    return { error: err.message, access_token: null, user_id: null, refresh_token: null };
  }
}

async function jsSignIn(email, password) {
  console.log("JS: Attempting signin for email:", email);
  try {
    const { data, error } = await supabase.auth.signInWithPassword({
      email: email,
      password: password,
    });

    if (error) {
      console.error("JS SignIn Error:", error);
      return { error: error.message, access_token: null, user_id: null, refresh_token: null };
    }

    console.log("JS SignIn Success:", data);
    const session = data.session;
    const user = data.user;
     if (session && user) {
         return {
            error: null,
            access_token: session.access_token,
            user_id: user.id,
            refresh_token: session.refresh_token
         };
    } else {
        console.error("JS SignIn: Unexpected response structure", data);
        return { error: "Unexpected signin response", access_token: null, user_id: null, refresh_token: null };
    }
  } catch (err) {
    console.error("JS SignIn Exception:", err);
    return { error: err.message, access_token: null, user_id: null, refresh_token: null };
  }
}

// Optional: Add jsSignOut if needed elsewhere
async function jsSignOut() {
    console.log("JS: Signing out...");
    const { error } = await supabase.auth.signOut();
    if (error) {
        console.error("JS SignOut Error:", error);
        return { error: error.message };
    }
    console.log("JS SignOut Successful");
    return { error: null };
}

// Optional: Add jsGetUser if needed to verify session from Python
async function jsGetUser() {
    console.log("JS: Getting current user session...");
    const { data: { session }, error } = await supabase.auth.getSession();
     if (error) {
        console.error("JS getSession Error:", error);
        return { error: error.message, user: null, session: null };
    }
    if (session) {
        console.log("JS getSession: Session found.");
        // Optionally get the full user object too
        const { data: { user } } = await supabase.auth.getUser();
        return { error: null, user: user, session: session };
    } else {
        console.log("JS getSession: No active session.");
        return { error: null, user: null, session: null };
    }
}
// --- Add these to supabase_wrappers.js ---

// --- Medal Count ---
async function jsGetMedalCount() {
    console.log("JS: Getting medal count...");
    try {
      // 1. Get User ID (essential for profile operations)
      const { data: { user }, error: userError } = await supabase.auth.getUser();
      if (userError || !user) {
        console.error("JS GetMedalCount Error: Cannot get user", userError);
        return { error: "Cannot get current user session", data: null };
      }
      const userId = user.id;
      console.log("JS GetMedalCount: User ID:", userId);
  
      // 2. Try fetching the profile
      const { data: profileData, error: fetchError } = await supabase
        .from('user_profiles')
        .select('medal_count')
        .eq('id', userId)
        .maybeSingle(); // Returns null if not found, doesn't error
  
      if (fetchError) {
        console.error("JS GetMedalCount Error fetching profile:", fetchError);
        return { error: fetchError.message, data: null };
      }
  
      console.log("JS GetMedalCount: Fetched profile data:", profileData);
  
      if (profileData !== null) {
        // Profile exists
        const count = profileData.medal_count !== null ? parseInt(profileData.medal_count, 10) : 0;
        console.log("JS GetMedalCount: Count from existing profile:", count);
        return { error: null, data: isNaN(count) ? 0 : count }; // Return 0 if count is invalid
      } else {
        // Profile doesn't exist, create it
        console.log("JS GetMedalCount: Profile not found, creating...");
        const { data: insertData, error: insertError } = await supabase
          .from('user_profiles')
          .insert({ id: userId, medal_count: 0 })
          .select('medal_count') // Select the count back to confirm
          .single(); // Expect one row back
  
        if (insertError) {
          // Handle potential race condition where profile was created between fetch and insert
          if (insertError.code === '23505') { // Unique violation code
               console.warn("JS GetMedalCount: Profile likely created concurrently. Assuming 0 medals.");
               return { error: null, data: 0 };
          }
          console.error("JS GetMedalCount Error inserting profile:", insertError);
          return { error: insertError.message, data: null };
        }
  
        console.log("JS GetMedalCount: Profile inserted:", insertData);
        const insertedCount = insertData ? parseInt(insertData.medal_count, 10) : 0;
        return { error: null, data: isNaN(insertedCount) ? 0 : insertedCount }; // Return 0 after creation
      }
    } catch (err) {
      console.error("JS GetMedalCount Exception:", err);
      return { error: err.message, data: null };
    }
  }
  
  async function jsUpdateMedalCountRpc(amountToAdd) {
    console.log("JS: Calling RPC increment_user_medal_count with amount:", amountToAdd);
    try {
      const { data, error } = await supabase.rpc('increment_user_medal_count', {
        amount_param: amountToAdd
      });
  
      if (error) {
        console.error("JS RPC Error:", error);
        return { error: error.message, data: null };
      }
  
      console.log("JS RPC Success:", data);
      // Assuming the RPC returns { success: true, new_medal_count: number } or { success: false, error: string }
      if (data && data.success === true && typeof data.new_medal_count === 'number') {
          return { error: null, data: data.new_medal_count };
      } else if (data && data.success === false) {
          return { error: data.error || "RPC indicated failure", data: null };
      } else {
          // Handle unexpected RPC return format
          console.warn("JS RPC: Unexpected response format", data);
          // Check if it might have returned just the number directly (older function version?)
          if (typeof data === 'number') {
               return { error: null, data: data };
          }
          return { error: "Unexpected RPC response format", data: null };
      }
    } catch (err) {
      console.error("JS RPC Exception:", err);
      return { error: err.message, data: null };
    }
  }
  
  
  // --- Tasks ---
  async function jsGetAllTasks() {
    console.log("JS: Getting all tasks...");
    try {
      const { data, error } = await supabase
        .from('tasks')
        .select('*'); // RLS handles user filtering
  
      if (error) {
        console.error("JS GetAllTasks Error:", error);
        return { error: error.message, data: null };
      }
      console.log("JS GetAllTasks Success:", data);
      return { error: null, data: data || [] }; // Return empty array if data is null
    } catch (err) {
      console.error("JS GetAllTasks Exception:", err);
      return { error: err.message, data: null };
    }
  }
  
  async function jsAddNewTask(taskData) { // taskData is JS object from Python dict
    console.log("JS: Adding new task:", taskData);
    try {
      // RLS should handle associating the task with the logged-in user (auth.uid())
      // Ensure taskData doesn't contain user_id unless your RLS specifically needs it passed
      const { data, error } = await supabase
        .from('tasks')
        .insert([taskData]) // Pass as an array
        .select(); // Select the inserted row back
  
      if (error) {
        console.error("JS AddNewTask Error:", error);
        return { error: error.message, data: null };
      }
      console.log("JS AddNewTask Success:", data);
      return { error: null, data: data }; // Returns an array with the inserted item(s)
    } catch (err) {
      console.error("JS AddNewTask Exception:", err);
      return { error: err.message, data: null };
    }
  }
  
  async function jsAddTaskHistory(historyData) {
    console.log("JS: Adding task history:", historyData);
    try {
      // RLS should handle user association
      const { data, error } = await supabase
        .from('task_history')
        .insert([historyData])
        .select();
  
      if (error) {
        console.error("JS AddTaskHistory Error:", error);
        return { error: error.message, data: null };
      }
      console.log("JS AddTaskHistory Success:", data);
      return { error: null, data: data };
    } catch (err) {
      console.error("JS AddTaskHistory Exception:", err);
      return { error: err.message, data: null };
    }
  }
  
  async function jsDeleteTask(taskId) {
    console.log("JS: Deleting task with ID:", taskId);
    try {
      const { error } = await supabase
        .from('tasks')
        .delete()
        .eq('id', taskId);
  
      if (error) {
        console.error("JS DeleteTask Error:", error);
        return { error: error.message };
      }
      console.log("JS DeleteTask Success");
      return { error: null }; // Indicate success
    } catch (err) {
      console.error("JS DeleteTask Exception:", err);
      return { error: err.message };
    }
  }
  
  // --- Rewards ---
  async function jsGetAllRewards() {
    console.log("JS: Getting all rewards...");
    try {
      const { data, error } = await supabase
        .from('rewards')
        .select('*'); // RLS handles user filtering
  
      if (error) {
        console.error("JS GetAllRewards Error:", error);
        return { error: error.message, data: null };
      }
      console.log("JS GetAllRewards Success:", data);
      return { error: null, data: data || [] };
    } catch (err) {
      console.error("JS GetAllRewards Exception:", err);
      return { error: err.message, data: null };
    }
  }
  
  async function jsAddNewReward(rewardData) {
    console.log("JS: Adding new reward:", rewardData);
    try {
      // RLS handles user association
      const { data, error } = await supabase
        .from('rewards')
        .insert([rewardData])
        .select();
  
      if (error) {
        console.error("JS AddNewReward Error:", error);
        return { error: error.message, data: null };
      }
      console.log("JS AddNewReward Success:", data);
      return { error: null, data: data };
    } catch (err) {
      console.error("JS AddNewReward Exception:", err);
      return { error: err.message, data: null };
    }
  }
  
  async function jsAddRewardHistory(historyData) {
    console.log("JS: Adding reward history:", historyData);
    try {
      // RLS handles user association
      const { data, error } = await supabase
        .from('reward_history')
        .insert([historyData])
        .select();
  
      if (error) {
        console.error("JS AddRewardHistory Error:", error);
        return { error: error.message, data: null };
      }
      console.log("JS AddRewardHistory Success:", data);
      return { error: null, data: data };
    } catch (err) {
      console.error("JS AddRewardHistory Exception:", err);
      return { error: err.message, data: null };
    }
  }
  
  async function jsDeleteReward(rewardId) {
    console.log("JS: Deleting reward with ID:", rewardId);
    try {
      const { error } = await supabase
        .from('rewards')
        .delete()
        .eq('id', rewardId);
  
      if (error) {
        console.error("JS DeleteReward Error:", error);
        return { error: error.message };
      }
      console.log("JS DeleteReward Success");
      return { error: null };
    } catch (err) {
      console.error("JS DeleteReward Exception:", err);
      return { error: err.message };
    }
  }
  
  // --- History Fetching ---
  async function jsGetTaskHistory() {
    console.log("JS: Getting task history...");
    try {
      const { data, error } = await supabase
        .from('task_history')
        .select('*')
        .order('timestamp', { ascending: false }); // RLS handles user filtering
  
      if (error) {
        console.error("JS GetTaskHistory Error:", error);
        return { error: error.message, data: null };
      }
      console.log("JS GetTaskHistory Success:", data);
      return { error: null, data: data || [] };
    } catch (err) {
      console.error("JS GetTaskHistory Exception:", err);
      return { error: err.message, data: null };
    }
  }
  
  async function jsGetRewardHistory() {
    console.log("JS: Getting reward history...");
    try {
      const { data, error } = await supabase
        .from('reward_history')
        .select('*')
        .order('timestamp', { ascending: false }); // RLS handles user filtering
  
      if (error) {
        console.error("JS GetRewardHistory Error:", error);
        return { error: error.message, data: null };
      }
      console.log("JS GetRewardHistory Success:", data);
      return { error: null, data: data || [] };
    } catch (err) {
      console.error("JS GetRewardHistory Exception:", err);
      return { error: err.message, data: null };
    }
  }
  