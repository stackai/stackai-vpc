--
-- Name: users add_user_to_org_sso; Type: TRIGGER; Schema: auth; Owner: supabase_auth_admin
--


CREATE TRIGGER add_user_to_org_sso AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION supabase_functions.http_request('http://stackend:8000/webhooks/new_user', 'POST', '{"Content-type":"application/json"}', '{}', '5000');
 
 
--   
-- Name: users on_auth_user_created; Type: TRIGGER; Schema: auth; Owner: supabase_auth_admin
--
        
CREATE TRIGGER on_auth_user_created AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
 
  
--
-- Name: users on_last_signed_in; Type: TRIGGER; Schema: auth; Owner: supabase_auth_admin
--
 
CREATE TRIGGER on_last_signed_in AFTER UPDATE ON auth.users FOR EACH ROW EXECUTE FUNCTION public.create_last_signed_in_on_profiles();


--
-- Name: profiles create_org_for_new_user; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER create_org_for_new_user AFTER INSERT ON public.profiles FOR EACH ROW EXECUTE FUNCTION public.create_org_and_map_user();


--
-- Name: profiles handle_null_organization; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER handle_null_organization AFTER INSERT ON public.profiles FOR EACH STATEMENT EXECUTE FUNCTION public.handle_empty_org();

ALTER TABLE public.profiles DISABLE TRIGGER handle_null_organization;