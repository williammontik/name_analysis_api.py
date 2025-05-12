# ── Analysis Endpoint ────────────────────────────────────────────────────────
@app.route("/analyze_name", methods=["POST"])
def analyze_name():
    data = request.get_json() if request.is_json else request.form

    try:
        # 1) Collect fields (unchanged)…
        name         = data.get("name", "").strip()
        chinese_name = data.get("chinese_name", "").strip()
        gender       = data.get("gender", "").strip()
        phone        = data.get("phone", "").strip()
        email        = data.get("email", "").strip()
        country      = data.get("country", "").strip()
        referrer     = data.get("referrer", "").strip()

        # 2) Reconstruct DOB string (unchanged)…
        day  = data.get("dob_day")
        mon  = data.get("dob_month")
        year = data.get("dob_year")
        if day and mon and year:
            # we'll parse these three separately below
            dob_day_str   = day
            dob_month_str = mon
            dob_year_str  = year
        else:
            # fallback to free‐form parser
            dob_input = data.get("dob", "").strip()
            parts = dob_input.split()
            # slightly modified below if someone passes English names…
            if len(parts) == 3:
                dob_day_str, dob_month_str, dob_year_str = parts
            else:
                # let dateutil handle more exotic formats
                birthdate = parser.parse(dob_input, dayfirst=True)
                dob_day_str   = str(birthdate.day)
                dob_month_str = str(birthdate.month)
                dob_year_str  = str(birthdate.year)

        app.logger.debug(f"Parsing DOB: day={dob_day_str!r}, month={dob_month_str!r}, year={dob_year_str!r}")

        # 3) Parse birthdate & compute age (UPDATED)
        # Strip any trailing '月' and convert to integer:
        month_key = dob_month_str.rstrip('月')
        # If someone passed a full English month name, try that too:
        try:
            month = int(month_key)
        except ValueError:
            # fallback: parse English month names (e.g. "February")
            import calendar
            month = list(calendar.month_name).index(month_key)
        day   = int(dob_day_str)
        year  = int(dob_year_str)
        birthdate = datetime(year, month, day)

        today = datetime.today()
        age = today.year - birthdate.year - (
            (today.month, today.day) < (birthdate.month, birthdate.day)
        )
        app.logger.debug(f"Computed birthdate={birthdate.date()}, age={age}")

        # 4) Notify by email (unchanged)…
        send_email(name, chinese_name, gender, birthdate.date(), age, phone, email, country, referrer)

        # 5) …rest of your logic remains the same…
        # generate metrics, call OpenAI, build JSON response

        return jsonify({
            "age_computed": age,
            # …
        })

    except Exception as e:
        app.logger.error("❌ Exception in /analyze_name", exc_info=True)
        return jsonify({ "error": str(e) }), 500
