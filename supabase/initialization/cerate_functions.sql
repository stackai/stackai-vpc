--
-- Name: create_last_signed_in_on_profiles(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.create_last_signed_in_on_profiles() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$
    begin
      IF (NEW.last_sign_in_at is null) THEN
        RETURN NULL;
      ELSE
        UPDATE public.profiles
        SET last_signed_in = NEW.last_sign_in_at
        WHERE id = (NEW.id)::uuid;
        RETURN NEW;
      END IF;
    end;
    $$;


ALTER FUNCTION public.create_last_signed_in_on_profiles() OWNER TO postgres;

--
-- Name: create_org_and_map_user(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.create_org_and_map_user() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$DECLARE
  new_org_id UUID;
  new_user_id UUID;
BEGIN
  -- Generate new organization ID
  new_org_id := gen_random_uuid();
  new_user_id := (NEW.id)::uuid;

  -- Insert into organizations table
  INSERT INTO public.organizations (org_id, org_name, org_plan)
  VALUES (new_org_id::text, '', 'free');

  -- Insert into user_organizations table
  INSERT INTO public.user_organizations (user_id, org_id)
  VALUES (new_user_id, new_org_id::text);  -- Cast UUID to text

  -- Remove after migration
  UPDATE public.profiles
  SET organization = new_org_id::text
  WHERE id = new_user_id;

  RETURN NEW;
END;$$;


ALTER FUNCTION public.create_org_and_map_user() OWNER TO postgres;

--
-- Name: handle_new_user(); Type: FUNCTION; Schema: public; Owner: postgres
--
  
CREATE FUNCTION public.handle_new_user() RETURNS trigger
    LANGUAGE plpgsql SECURITY DEFINER
    AS $$begin
  insert into public.profiles (id, full_name, avatar_url, is_manager, organization, email, last_signed_in)
  values (new.id, new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'avatar_url', new.raw_user_meta_data->>'is_manager', new.raw_user_meta_data->>'organization', new.email, new.last_sign_in_at);
  return new;
end;
$$;
 
    
ALTER FUNCTION public.handle_new_user() OWNER TO postgres;

--
-- Name: handle_empty_org(); Type: FUNCTION; Schema: public; Owner: postgres
--
 
CREATE FUNCTION public.handle_empty_org() RETURNS trigger
    LANGUAGE plpgsql
    AS $$declare
  new_org_id UUID;
  user_id UUID;
begin
  -- Check if organization is NULL
  IF NEW.organization IS NULL THEN
    -- Generate new organization ID
    new_org_id := uuid_generate_v4();
    user_id := NEW.id;
 
    -- Insert into organizations
    INSERT INTO organizations (org_id, org_name, org_plan)
    VALUES (new_org_id, '', 'free');
  
    -- Insert into user_organizations
    INSERT INTO user_organizations (user_id, org_id)
    VALUES (user_id, new_org_id);    
    
    -- Update the profiles table
    UPDATE profiles
    SET organization = new_org_id
    WHERE id = user_id;
  
    -- Return the new organization ID
    RETURN NEW;
  END IF;
  RETURN NULL;
END;
$$;

 
ALTER FUNCTION public.handle_empty_org() OWNER TO postgres;